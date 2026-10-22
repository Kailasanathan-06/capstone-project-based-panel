"""
MEC Manager - API Views.

Implements:
- POST  /api/mec/register/          -> one-time pairing registration
- POST  /api/mec/heartbeat/         -> authenticated heartbeat + telemetry
- GET   /api/mec/                   -> list devices (dynamic)
- GET   /api/mec/<id>/              -> device detail with live telemetry
- POST  /api/mec/<id>/revoke/       -> revoke a device (blocks dispatch)
- POST  /api/mec/<id>/unrevoke/
- GET   /api/mec/pairing-codes/     -> list pairing codes (staff/logged-in)
- POST  /api/mec/pairing-codes/     -> generate a new pairing code
- GET   /api/mec/<id>/task/         -> next assigned task for the device
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token

from .models import MECAgent, PairingCode, generate_device_id
from .serializers import (
    MECAgentSerializer,
    MECAgentDetailSerializer,
    HeartbeatSerializer,
    PairingCodeSerializer,
    RegisterRequestSerializer,
)
from .services import (
    refresh_mec_status,
    register_mec,
    process_heartbeat,
    requeue_orphaned_tasks,
)
from tasks.models import Task


class MECAuthentication(TokenAuthentication):
    """Authenticates a MEC device using its DRF token plus X-MEC-ID header."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, token = result
        mec_id = request.META.get("HTTP_X_MEC_ID", "")
        if not mec_id:
            return None
        try:
            agent = MECAgent.objects.get(device_id=mec_id, user=user)
            if agent.is_revoked:
                return None
        except MECAgent.DoesNotExist:
            return None
        request.mec_agent = agent
        return (user, token)


class MECAgentViewSet(viewsets.ViewSet):
    """Operations on registered MEC devices."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Registration and heartbeat are protected by the pairing code / device
        # credentials (validated inside the business logic) rather than a login.
        if getattr(self, "action", None) in ("register", "heartbeat"):
            return [AllowAny()]
        return super().get_permissions()

    def list(self, request):
        """Dynamically list every registered MEC device."""
        refresh_mec_status()
        requeue_orphaned_tasks()
        agents = MECAgent.objects.all().select_related()
        serializer = MECAgentDetailSerializer(agents, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get one device by its MEC-XXX id."""
        refresh_mec_status()
        try:
            agent = MECAgent.objects.get(device_id=pk)
        except MECAgent.DoesNotExist:
            return Response({"error": "MEC device not found"}, status=404)
        return Response(MECAgentDetailSerializer(agent).data)

    def register(self, request):
        """One-time device registration guarded by a pairing code."""
        serializer = RegisterRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ip = request.META.get("REMOTE_ADDR", "")
        agent, auth_token, error = register_mec(
            pairing_code=serializer.validated_data["pairing_code"],
            system_name=serializer.validated_data.get("system_name", ""),
            server_url=serializer.validated_data.get("server_url", ""),
            agent_version=serializer.validated_data.get("agent_version", "1.0.0"),
            ip=ip,
        )
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=agent.user)
        return Response(
            {
                "device_id": agent.device_id,
                "auth_token": auth_token,
                "token": token.key,
                "server_url": agent.server_url,
                "heartbeat_interval": 10,
                "heartbeat_timeout": 30,
                "status": "registered",
            },
            status=status.HTTP_201_CREATED,
        )

    def heartbeat(self, request):
        """Process a heartbeat (also acts as the online/offline signal)."""
        agent, beat = process_heartbeat(
            device_id=request.data.get("mec_id", ""),
            auth_token=request.data.get("auth_token", ""),
            payload=request.data,
            request_ip=request.META.get("REMOTE_ADDR", ""),
        )
        if not agent:
            from engine.hospital_workloads import record_security_event

            dev_id = request.data.get("mec_id", "")
            ip = request.META.get("REMOTE_ADDR", "")
            record_security_event(
                event_type="INVALID_MEC_AUTH",
                severity="CRITICAL",
                description=f"MEC device heartbeat rejected: invalid or expired credentials for device '{dev_id}'",
                device_id=dev_id,
                source_ip=ip,
                details=dict(request.data) if hasattr(request, "data") and isinstance(request.data, dict) else {},
                blocked=True,
            )
            return Response(
                {"error": "Authentication failed - invalid device or token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "device_id": agent.device_id,
                "status": "ONLINE" if agent.is_online else "OFFLINE",
                "last_seen": agent.last_seen,
                "next_action": "acknowledged",
            }
        )

    def revoke(self, request, pk=None):
        """Revoke a device - it becomes BLOCKED and never receives tasks."""
        try:
            agent = MECAgent.objects.get(device_id=pk)
        except MECAgent.DoesNotExist:
            return Response({"error": "MEC device not found"}, status=404)
        agent.is_revoked = True
        agent.is_online = False
        agent.save(update_fields=["is_revoked", "is_online"])
        requeue_orphaned_tasks()
        return Response({"device_id": agent.device_id, "status": "REVOKED", "blocked": True})

    def unrevoke(self, request, pk=None):
        try:
            agent = MECAgent.objects.get(device_id=pk)
        except MECAgent.DoesNotExist:
            return Response({"error": "MEC device not found"}, status=404)
        agent.is_revoked = False
        agent.save(update_fields=["is_revoked"])
        return Response({"device_id": agent.device_id, "status": "UNREVOKED"})


class PairingCodeViewSet(viewsets.ViewSet):
    """Generate and list one-time pairing codes."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        codes = PairingCode.objects.all()
        return Response(PairingCodeSerializer(codes, many=True).data)

    def create(self, request):
        code = PairingCode.generate_new()
        code.description = request.data.get("description", "")
        code.save()
        return Response(PairingCodeSerializer(code).data, status=status.HTTP_201_CREATED)


class MECHeartbeatViewSet(viewsets.ViewSet):
    """Heartbeat history for a device (dashboard consumption)."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        mec_id = request.query_params.get("mec_id", "")
        beats = MECAgent.objects.get(device_id=mec_id).heartbeats.all()[:50]
        return Response(HeartbeatSerializer(beats, many=True).data)


class MECTaskEndpoint(viewsets.ViewSet):
    """
    Lets an authenticated MEC pull its next assigned task and mark results.
    """

    authentication_classes = [MECAuthentication]
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request, message=None, code=None):
        from engine.hospital_workloads import record_security_event

        dev_id = request.META.get("HTTP_X_MEC_ID", "") or (
            request.data.get("mec_id", "") if hasattr(request, "data") and isinstance(request.data, dict) else ""
        )
        ip = request.META.get("REMOTE_ADDR", "")
        record_security_event(
            event_type="INVALID_MEC_AUTH",
            severity="CRITICAL",
            description=f"Unauthorized MEC task access attempt: invalid or missing credentials for device '{dev_id}'",
            device_id=dev_id,
            source_ip=ip,
            details={"device_id": dev_id},
            blocked=True,
        )
        super().permission_denied(request, message=message, code=code)

    def next_task(self, request, pk=None):
        """Return the task currently assigned to this MEC (if any)."""
        from tasks.serializers import TaskSerializer

        agent = request.mec_agent
        task = Task.objects.filter(assigned_mec=agent, status__in=["ASSIGNED", "RUNNING"]).first()
        if not task:
            return Response({"task": None})
        return Response({"task": TaskSerializer(task).data})

    def report_result(self, request, pk=None):
        """MEC reports task completion / failure with measured telemetry."""
        from tasks.serializers import TaskSerializer

        agent = request.mec_agent
        task_id = request.data.get("task_id", "")
        try:
            task = Task.objects.get(task_id=task_id, assigned_mec=agent)
        except Task.DoesNotExist:
            return Response({"error": "Task not found or not assigned to this MEC"}, status=404)

        task.execution_time = float(request.data.get("execution_time", 0.0))
        task.actual_cpu = request.data.get("cpu_usage")
        task.actual_ram = request.data.get("ram_usage")
        task.network_latency = request.data.get("network_latency")
        task.estimated_energy = request.data.get("estimated_energy", 0.0)
        task.result_location = request.data.get("result_location", "")
        if request.data.get("output_path"):
            task.output_path = request.data.get("output_path")
        if request.data.get("output_checksum"):
            task.output_checksum = request.data.get("output_checksum")
        if request.data.get("input_checksum"):
            task.input_checksum = request.data.get("input_checksum")
        if request.data.get("image_processing_time"):
            task.image_processing_time = float(request.data.get("image_processing_time", 0.0))
        task.total_latency_ms = (task.execution_time * 1000.0) if task.execution_time else 0.0
        task.is_simulated_execution = False

        if request.data.get("success") or request.data.get("status") == "COMPLETED":
            task.status = "COMPLETED"
            task.record_history("RUNNING", "COMPLETED", changed_by=agent.device_id)
        else:
            task.status = "FAILED"
            task.error_message = request.data.get("error_message", "")
            task.record_history("RUNNING", "FAILED", changed_by=agent.device_id)

        task.save()
        return Response(TaskSerializer(task).data)