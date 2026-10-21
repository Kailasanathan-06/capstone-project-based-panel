"""
MEC Manager - Models for MEC agent registration, pairing, heartbeat and device identity.

A MEC device registers ONCE using a pairing code. The server generates a unique
device ID (MEC-XXX) and a secure authentication token. The IP address is stored
only as diagnostic information - it is never used as the device identity.
"""

import secrets
import re

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def generate_device_id():
    for i in range(1, 9999):
        candidate = f"MEC-{i:03d}"
        if not MECAgent.objects.filter(device_id=candidate).exists():
            return candidate
    return f"MEC-{secrets.randbelow(9999):04d}"


class MECAgent(models.Model):
    """Registered MEC agent with authentication credentials."""

    # Unique device ID (NOT the IP address)
    device_id = models.CharField("MEC Device ID", max_length=20, unique=True)
    # Human-readable system name
    system_name = models.CharField("System Name", max_length=100, blank=True)
    # Secure authentication token used on every request
    auth_token = models.CharField("Authentication Token", max_length=128, unique=True)
    # Django user account owning this device (optional)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # Server URL this agent connects to (stored for diagnostics / reconnection)
    server_url = models.CharField("Server URL", max_length=255, default="http://127.0.0.1:8000")
    # Online / offline bookkeeping
    last_heartbeat = models.DateTimeField("Last Heartbeat", null=True, blank=True)
    last_seen = models.DateTimeField("Last Seen", null=True, blank=True)
    is_online = models.BooleanField("Online Status", default=False)
    is_revoked = models.BooleanField("Revoked", default=False)
    # System information (diagnostics)
    hostname = models.CharField("Hostname", max_length=100, blank=True)
    operating_system = models.CharField("Operating System", max_length=50, blank=True)
    agent_version = models.CharField("Agent Version", max_length=20, default="1.0.0")
    registered_at = models.DateTimeField("Registered At", default=timezone.now)
    # IP is diagnostic ONLY - never the primary identity
    last_known_ip = models.GenericIPAddressField("Last Known IP (diagnostic)", null=True, blank=True)

    class Meta:
        verbose_name = "MEC Agent"
        verbose_name_plural = "MEC Agents"
        ordering = ["device_id"]

    def __str__(self):
        return f"{self.device_id} - {'ONLINE' if self.is_online else 'OFFLINE'}"

    @property
    def is_eligible(self):
        """A device may only execute tasks when online and NOT revoked."""
        return self.is_online and not self.is_revoked

    @property
    def status_label(self):
        if self.is_revoked:
            return "REVOKED"
        return "ONLINE" if self.is_online else "OFFLINE"


class PairingCode(models.Model):
    """One-time registration key that authorizes a new MEC device."""

    code = models.CharField("Pairing Code", max_length=32, unique=True)
    description = models.CharField("Description", max_length=200, blank=True)
    is_used = models.BooleanField("Used", default=False)
    used_by = models.CharField("Used By", max_length=20, blank=True)
    created_at = models.DateTimeField("Created At", default=timezone.now)
    used_at = models.DateTimeField("Used At", null=True, blank=True)

    class Meta:
        verbose_name = "Pairing Code"
        verbose_name_plural = "Pairing Codes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def generate_new():
        """Create and return a fresh unused pairing code."""
        code = "SDT-" + secrets.token_hex(4).upper() + "-" + secrets.token_hex(2).upper()
        return PairingCode.objects.create(code=code)


class Heartbeat(models.Model):
    """Heartbeat records for online/offline status tracking."""

    mec = models.ForeignKey(MECAgent, on_delete=models.CASCADE, related_name="heartbeats")
    timestamp = models.DateTimeField("Timestamp")
    cpu_usage = models.FloatField("CPU Usage (%)", default=0.0)
    ram_usage = models.FloatField("RAM Usage (%)", default=0.0)
    disk_usage = models.FloatField("Disk Usage (%)", default=0.0)
    available_storage = models.FloatField("Available Storage (GB)", default=0.0)
    current_task = models.CharField("Current Task", max_length=50, blank=True)
    status = models.CharField("Status", max_length=20, default="ONLINE")
    # Additional telemetry
    hostname = models.CharField("Hostname", max_length=100, blank=True)
    os_info = models.CharField("OS Info", max_length=100, blank=True)
    cpu_info = models.CharField("CPU Info", max_length=100, blank=True)
    storage_info = models.CharField("Storage Info", max_length=100, blank=True)
    processor_info = models.CharField("Processor Info", max_length=100, blank=True)
    task_count = models.IntegerField("Task Count", default=0)
    network_latency = models.FloatField("Network Latency (ms)", default=0.0)
    energy_estimate = models.FloatField("Estimated Energy (Wh)", default=0.0)

    class Meta:
        verbose_name = "Heartbeat"
        verbose_name_plural = "Heartbeats"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.mec.device_id} @ {self.timestamp}"