"""
Tasks - Serializers for task management.

`assigned_mec` is exposed as the MEC-XXX device id, and writeable via that id.
"""

from rest_framework import serializers
from .models import Task
from mec_manager.models import MECAgent


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model."""

    task_id = serializers.CharField(read_only=True)
    assigned_mec = serializers.SlugRelatedField(
        slug_field="device_id",
        queryset=MECAgent.objects.all(),
        required=False,
        allow_null=True,
    )
    assigned_mec_detail = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "task_id", "name", "priority", "data_size_mb", "cpu_cycles_giga",
            "memory_mb", "deadline_ms", "privacy_sensitivity", "security_sensitivity",
            "status", "assigned_mec", "assigned_mec_detail", "execute_in_cloud",
            "execution_time", "error_message", "result_location", "estimated_energy",
            "created_at", "updated_at"
        ]

    def get_assigned_mec_detail(self, obj):
        if obj.assigned_mec:
            from mec_manager.serializers import MECAgentSerializer
            return MECAgentSerializer(obj.assigned_mec).data
        return None

    def validate(self, data):
        """Validation based on the target MEC's real status."""
        mec = data.get("assigned_mec")
        if mec:
            from mec_manager.services import refresh_mec_status
            refresh_mec_status()
            if mec.is_revoked:
                raise serializers.ValidationError(
                    {"assigned_mec": "This MEC device is REVOKED. Assignment to revoked devices is forbidden."}
                )
            if not mec.is_eligible:
                raise serializers.ValidationError(
                    {"assigned_mec": "MEC agent is OFFLINE. Tasks can only be assigned to ONLINE devices."}
                )
        return data