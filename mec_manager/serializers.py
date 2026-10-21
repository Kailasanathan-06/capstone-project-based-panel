"""
MEC Manager - Serializers.

The public serializers never expose the authentication token. Device identity
is the MEC-XXX id, not the IP address.
"""

from rest_framework import serializers
from .models import MECAgent, Heartbeat, PairingCode


class MECAgentSerializer(serializers.ModelSerializer):
    """Public representation of a registered MEC device."""

    status = serializers.CharField(source="status_label", read_only=True)

    class Meta:
        model = MECAgent
        fields = [
            "device_id",
            "system_name",
            "agent_version",
            "is_online",
            "is_revoked",
            "status",
            "last_seen",
            "last_heartbeat",
            "hostname",
            "operating_system",
            "server_url",
            "registered_at",
            "last_known_ip",
        ]


class MECAgentDetailSerializer(MECAgentSerializer):
    """MEC device joined with its most recent heartbeat telemetry."""

    cpu = serializers.SerializerMethodField()
    ram = serializers.SerializerMethodField()
    disk = serializers.SerializerMethodField()
    storage = serializers.SerializerMethodField()
    latency = serializers.SerializerMethodField()
    energy = serializers.SerializerMethodField()
    current_task = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta(MECAgentSerializer.Meta):
        fields = MECAgentSerializer.Meta.fields + [
            "cpu",
            "ram",
            "disk",
            "storage",
            "latency",
            "energy",
            "current_task",
            "task_count",
        ]

    def _latest_beat(self, obj):
        return obj.heartbeats.order_by("-timestamp").first()

    def get_cpu(self, obj):
        beat = self._latest_beat(obj)
        return round(beat.cpu_usage, 1) if beat else 0.0

    def get_ram(self, obj):
        beat = self._latest_beat(obj)
        return round(beat.ram_usage, 1) if beat else 0.0

    def get_disk(self, obj):
        beat = self._latest_beat(obj)
        return round(beat.disk_usage, 1) if beat else 0.0

    def get_storage(self, obj):
        beat = self._latest_beat(obj)
        return round(beat.available_storage, 1) if beat else 0.0

    def get_latency(self, obj):
        beat = self._latest_beat(obj)
        return round(beat.network_latency, 1) if beat else 0.0

    def get_energy(self, obj):
        beat = self._latest_beat(obj)
        return round(beat.energy_estimate, 3) if beat else 0.0

    def get_current_task(self, obj):
        beat = self._latest_beat(obj)
        return beat.current_task if beat else ""

    def get_task_count(self, obj):
        beat = self._latest_beat(obj)
        return beat.task_count if beat else 0


class HeartbeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Heartbeat
        fields = [
            "id",
            "mec",
            "timestamp",
            "cpu_usage",
            "ram_usage",
            "disk_usage",
            "available_storage",
            "current_task",
            "status",
            "hostname",
            "os_info",
            "cpu_info",
            "processor_info",
            "task_count",
            "network_latency",
            "energy_estimate",
        ]
        read_only_fields = ["id", "timestamp"]


class PairingCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PairingCode
        fields = ["code", "description", "is_used", "used_by", "created_at", "used_at"]
        read_only_fields = ["code", "is_used", "used_by", "created_at", "used_at"]


class RegisterRequestSerializer(serializers.Serializer):
    """Payload sent by the MEC Agent during its one-time registration."""

    pairing_code = serializers.CharField(max_length=32)
    system_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    server_url = serializers.CharField(max_length=255, required=False, allow_blank=True)
    agent_version = serializers.CharField(max_length=20, required=False, allow_blank=True)