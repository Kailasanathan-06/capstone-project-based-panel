"""
Tasks - Models for the task queue with online/offline awareness.

Task lifecycle:
PENDING -> QUEUED -> ASSIGNED -> RUNNING -> COMPLETED
                    (FAILED -> QUEUED for reassignment)
                    (CANCELLED terminates the task)

If the assigned MEC goes offline the task is automatically returned to QUEUED
so the GA scheduler can reassign it to another ONLINE eligible device.
"""

from django.db import models
from django.utils import timezone


class Task(models.Model):
    """A unit of work that must be executed by an ONLINE MEC or the cloud."""

    STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("QUEUED", "QUEUED"),
        ("ASSIGNED", "ASSIGNED"),
        ("RUNNING", "RUNNING"),
        ("COMPLETED", "COMPLETED"),
        ("FAILED", "FAILED"),
        ("CANCELLED", "CANCELLED"),
        ("RETRYING", "RETRYING"),
    ]

    task_id = models.CharField("Task ID", max_length=50, unique=True)
    name = models.CharField("Task Name", max_length=200)
    # Priority (lower = higher priority)
    priority = models.IntegerField("Priority", default=1)
    # Workload description
    data_size_mb = models.FloatField("Data Size (MB)", default=0.0)
    cpu_cycles_giga = models.FloatField("CPU Cycles (Giga)", default=0.0)
    memory_mb = models.IntegerField("Memory (MB)", default=0)
    deadline_ms = models.IntegerField("Deadline (ms)", default=0)
    # Privacy sensitivity 0..1 (0 = public, 1 = highly sensitive)
    privacy_sensitivity = models.FloatField("Privacy Sensitivity", default=0.0)
    # Security sensitivity 0..1
    security_sensitivity = models.FloatField("Security Sensitivity", default=0.0)
    status = models.CharField("Status", max_length=20, default="PENDING", choices=STATUS_CHOICES)
    assigned_mec = models.ForeignKey(
        "mec_manager.MECAgent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    execute_in_cloud = models.BooleanField("Execute in Cloud", default=False)
    # Execution results (real measurements / estimated energy)
    execution_time = models.FloatField("Execution Time (s)", null=True, blank=True)
    actual_cpu = models.FloatField("Actual CPU (%)", null=True, blank=True)
    actual_ram = models.FloatField("Actual RAM (%)", null=True, blank=True)
    network_latency = models.FloatField("Network Latency (ms)", null=True, blank=True)
    estimated_energy = models.FloatField("Estimated Energy (Wh)", default=0.0)
    # Google Drive file id of the generated result
    result_location = models.CharField("Result Location (Google Drive ID)", max_length=200, blank=True)
    error_message = models.TextField("Error Message", blank=True)
    created_at = models.DateTimeField("Created At", default=timezone.now)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["priority", "-created_at"]

    def __str__(self):
        return f"{self.task_id}: {self.name} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.task_id:
            self.task_id = generate_task_id()
        super().save(*args, **kwargs)

    def record_history(self, from_status, to_status, changed_by="system"):
        TaskQueueHistory.objects.create(
            task=self,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
        )

    @property
    def online_eligible(self):
        """A task may only execute when its assigned MEC is ONLINE and not revoked."""
        if self.status in ("COMPLETED", "FAILED", "CANCELLED"):
            return False
        if self.assigned_mec:
            return self.assigned_mec.is_eligible
        # Not yet assigned - the GA will pick an online device.
        return True

    def requeue_if_offline(self):
        """
        If the task is ASSIGNED/RUNNING and its MEC is no longer online,
        release it back to QUEUED so it can be re-dispatched.
        Returns True if the task was requeued.
        """
        if self.status in ("ASSIGNED", "RUNNING") and self.assigned_mec:
            if not self.assigned_mec.is_eligible:
                previous = self.status
                self.status = "QUEUED"
                self.assigned_mec = None
                self.save(update_fields=["status", "assigned_mec", "updated_at"])
                self.record_history(previous, "QUEUED", changed_by="auto_offline")
                return True
        return False


def generate_task_id():
    from datetime import datetime
    import secrets

    return "TASK-" + datetime.now().strftime("%Y%m%d%H%M%S") + secrets.token_hex(2).upper()


class TaskQueueHistory(models.Model):
    """Audit trail of every task state transition."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="queue_history")
    from_status = models.CharField("From Status", max_length=20)
    to_status = models.CharField("To Status", max_length=20)
    changed_at = models.DateTimeField("Changed At", default=timezone.now)
    changed_by = models.CharField("Changed By", max_length=100, blank=True)

    class Meta:
        verbose_name = "Task Queue History"
        verbose_name_plural = "Task Queue Histories"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.task.task_id}: {self.from_status} -> {self.to_status}"