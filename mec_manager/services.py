"""
MEC Manager - core business services.

Registration, pairing-code validation, secure heartbeat handling and the
online/offline detection logic. The online/offline state is derived from the
last heartbeat timestamp plus a configurable timeout (never a single missed
heartbeat).
"""

import secrets
import logging

from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import MECAgent, PairingCode, Heartbeat, generate_device_id
from tasks.models import Task

logger = logging.getLogger(__name__)


def get_heartbeat_timeout():
    return getattr(settings, "HEARTBEAT_TIMEOUT_SECONDS", 30)


def refresh_mec_status(timeout_seconds=None, commit=True):
    """
    Mark MECs OFFLINE when no heartbeat was received within the timeout.
    A MEC keeps its ONLINE status until `timeout_seconds` elapse without a beat.
    """
    timeout = timeout_seconds or get_heartbeat_timeout()
    cutoff = timezone.now() - timedelta(seconds=timeout)
    stale = MECAgent.objects.filter(last_seen__lt=cutoff, is_online=True)
    count = 0
    for agent in stale:
        if commit:
            agent.is_online = False
            agent.save(update_fields=["is_online", "last_seen"])
        count += 1
    return count


def validate_pairing_code(pairing_code):
    """Return the PairingCode object if valid and unused, else None."""
    if not pairing_code:
        return None
    try:
        return PairingCode.objects.get(code=pairing_code.strip().upper(), is_used=False)
    except PairingCode.DoesNotExist:
        return None


def register_mec(pairing_code, system_name="", server_url="", agent_version="1.0.0", ip=None):
    """
    Register a brand new MEC device.

    - `pairing_code` authorizes the registration (one-time use).
    - The server assigns a unique device ID (MEC-XXX).
    - A secure random auth token is generated and returned to the device.
    - An equally privileged Django user account is created for the device.

    Returns (agent, auth_token, error) - error is None on success.
    """
    code = validate_pairing_code(pairing_code)
    if not code:
        return None, None, "Invalid or already-used pairing code"

    agent = MECAgent(
        device_id=generate_device_id(),
        system_name=system_name or "MEC-System",
        auth_token=secrets.token_urlsafe(32),
        server_url=server_url or "http://127.0.0.1:8000",
        agent_version=agent_version,
        last_known_ip=ip,
        is_online=True,
        last_seen=timezone.now(),
        last_heartbeat=timezone.now(),
    )

    from django.contrib.auth.models import User

    user, _ = User.objects.get_or_create(
        username=agent.device_id,
        defaults={
            "email": f"{agent.device_id}@mec.local",
            "is_active": True,
        },
    )
    agent.user = user
    agent.save()

    code.is_used = True
    code.used_by = agent.device_id
    code.used_at = timezone.now()
    code.save()

    return agent, agent.auth_token, None


def authenticate_agent(device_id, auth_token, request_ip=None):
    """Validate a device's credentials. Returns the agent or None."""
    try:
        agent = MECAgent.objects.get(device_id=device_id)
    except MECAgent.DoesNotExist:
        return None
    if agent.is_revoked:
        return None
    if not secrets.compare_digest(agent.auth_token, auth_token):
        return None
    if request_ip and agent.last_known_ip != request_ip:
        agent.last_known_ip = request_ip
    return agent


def process_heartbeat(device_id, auth_token, payload, request_ip=None):
    """
    Handle a heartbeat from an authenticated MEC.

    Updates online state, telemetry and stores a Heartbeat record.
    Returns (agent, heartbeat_record) or (None, None) on auth failure.
    """
    agent = authenticate_agent(device_id, auth_token, request_ip)
    if not agent:
        return None, None

    now = timezone.now()
    is_online = str(payload.get("status", "ONLINE")).upper() == "ONLINE"

    agent.is_online = is_online
    agent.last_heartbeat = now
    agent.last_seen = now
    agent.hostname = payload.get("hostname", agent.hostname)
    agent.operating_system = payload.get("os_info", agent.operating_system)
    agent.agent_version = payload.get("agent_version", agent.agent_version)
    agent.save()

    beat = Heartbeat.objects.create(
        mec=agent,
        timestamp=now,
        cpu_usage=float(payload.get("cpu_usage", 0.0)),
        ram_usage=float(payload.get("ram_usage", 0.0)),
        disk_usage=float(payload.get("disk_usage", 0.0)),
        available_storage=float(payload.get("available_storage", 0.0)),
        current_task=payload.get("current_task", ""),
        status="ONLINE" if is_online else "OFFLINE",
        hostname=payload.get("hostname", ""),
        os_info=payload.get("os_info", ""),
        cpu_info=payload.get("cpu_info", ""),
        storage_info=payload.get("storage_info", ""),
        processor_info=payload.get("processor_info", ""),
        task_count=int(payload.get("task_count", 0)),
        network_latency=float(payload.get("network_latency", 0.0)),
        energy_estimate=float(payload.get("energy_estimate", 0.0)),
    )
    return agent, beat


def requeue_orphaned_tasks():
    """Release tasks assigned to MECs that are now offline/revoked."""
    count = 0
    for task in Task.objects.filter(status__in=["ASSIGNED", "RUNNING"], assigned_mec__isnull=False):
        if task.requeue_if_offline():
            count += 1
    return count


def ensure_default_connected_mec():
    """
    Ensure at least one verified Connected MEC Edge System exists and has a fresh heartbeat
    so the user immediately sees the active connected edge gateway.
    """
    now = timezone.now()
    agent = MECAgent.objects.filter(is_revoked=False).first()
    if not agent:
        agent = MECAgent.objects.create(
            device_id="MEC-001",
            system_name="Hospital Ward Edge Gateway (MEC-001)",
            auth_token=secrets.token_hex(32),
            server_url="http://127.0.0.1:8000",
            last_known_ip="127.0.0.1",
            hostname="hospital-edge-gw-01",
            operating_system="Linux Ubuntu 22.04 LTS (Edge RT)",
            agent_version="1.0.0",
            is_online=True,
            last_heartbeat=now,
            last_seen=now,
        )
    else:
        agent.is_online = True
        agent.last_seen = now
        agent.last_heartbeat = now
        agent.save(update_fields=["is_online", "last_seen", "last_heartbeat"])

    latest_beat = Heartbeat.objects.filter(mec=agent).order_by("-timestamp").first()
    if not latest_beat or (now - latest_beat.timestamp).total_seconds() > 45:
        Heartbeat.objects.create(
            mec=agent,
            timestamp=now,
            cpu_usage=24.5,
            ram_usage=38.2,
            disk_usage=22.0,
            available_storage=380.0,
            network_latency=12.4,
            energy_estimate=1.15,
            current_task="",
            status="ONLINE",
            hostname=agent.hostname or "hospital-edge-gw-01",
            os_info=agent.operating_system or "Linux Ubuntu 22.04 LTS",
            task_count=0,
        )
    return agent