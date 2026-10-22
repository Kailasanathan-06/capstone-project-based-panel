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
        ("CREATED", "CREATED"),
        ("VALIDATING", "VALIDATING"),
        ("PENDING", "PENDING"),
        ("QUEUED", "QUEUED"),
        ("SCHEDULED", "SCHEDULED"),
        ("ASSIGNED", "ASSIGNED"),
        ("RUNNING", "RUNNING"),
        ("SUCCEEDED", "SUCCEEDED"),
        ("COMPLETED", "COMPLETED"),
        ("FAILED", "FAILED"),
        ("TIMED_OUT", "TIMED_OUT"),
        ("CANCELLED", "CANCELLED"),
        ("REJECTED", "REJECTED"),
        ("BLOCKED", "BLOCKED"),
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
    # Explicit task placement policy
    PRIVACY_POLICY_CHOICES = [
        ("LOCAL_ONLY", "LOCAL_ONLY"),
        ("TRUSTED_EDGE", "TRUSTED_EDGE"),
        ("CLOUD_ALLOWED", "CLOUD_ALLOWED"),
    ]
    privacy_policy = models.CharField(
        "Privacy Policy",
        max_length=20,
        default="TRUSTED_EDGE",
        choices=PRIVACY_POLICY_CHOICES,
    )
    status = models.CharField("Status", max_length=20, default="PENDING", choices=STATUS_CHOICES)
    assigned_mec = models.ForeignKey(
        "mec_manager.MECAgent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    # Selected resource ID (LOCAL, MEC-XXX, CLOUD) and Tier
    assigned_node = models.CharField("Assigned Node", max_length=50, blank=True, default="")
    assigned_tier = models.CharField("Assigned Tier", max_length=20, blank=True, default="")
    execute_in_cloud = models.BooleanField("Execute in Cloud", default=False)
    # Medical Image Preprocessing Workload fields
    image_path = models.CharField("Image Path", max_length=500, blank=True, default="")
    operation = models.CharField("Operation", max_length=50, default="normalize_clahe")
    target_resolution = models.IntegerField("Target Resolution", default=224)
    input_checksum = models.CharField("Input Checksum (SHA-256)", max_length=64, blank=True, default="")
    output_checksum = models.CharField("Output Checksum (SHA-256)", max_length=64, blank=True, default="")
    output_path = models.CharField("Output Path", max_length=500, blank=True, default="")
    dataset_sample_id = models.CharField("Dataset Sample ID", max_length=100, blank=True, default="")
    scheduler_algorithm = models.CharField("Scheduler Algorithm", max_length=50, blank=True, default="proposed_ga")
    scheduler_runtime_ms = models.FloatField("Scheduler Runtime (ms)", default=0.0)
    image_processing_time = models.FloatField("Image Processing Time (s)", default=0.0)
    total_latency_ms = models.FloatField("Total Latency (ms)", default=0.0)
    is_simulated_execution = models.BooleanField("Is Simulated Execution", default=False)
    # Execution results (real measurements / estimated energy)
    execution_time = models.FloatField("Execution Time (s)", null=True, blank=True)
    actual_cpu = models.FloatField("Actual CPU (%)", null=True, blank=True)
    actual_ram = models.FloatField("Actual RAM (%)", null=True, blank=True)
    network_latency = models.FloatField("Network Latency (ms)", null=True, blank=True)
    estimated_energy = models.FloatField("Estimated Energy (Wh)", default=0.0)
    # Google Drive file id of the generated result
    result_location = models.CharField("Result Location (Google Drive ID)", max_length=200, blank=True)
    error_message = models.TextField("Error Message", blank=True)
    # Hospital Workload Scenario and Execution Tracking
    scenario_id = models.CharField("Scenario ID", max_length=60, blank=True, default="")
    workload_category = models.CharField("Workload Category", max_length=30, blank=True, default="SUCCESS")
    workload_type = models.CharField("Workload Type", max_length=60, blank=True, default="medical_image_preprocess")
    error_code = models.CharField("Error Code", max_length=50, blank=True, default="")
    timeout_limit_seconds = models.IntegerField("Timeout Limit (s)", default=60)
    retry_count = models.IntegerField("Retry Count", default=0)
    max_retries = models.IntegerField("Max Retries", default=3)
    start_time = models.DateTimeField("Start Time", null=True, blank=True)
    completion_time = models.DateTimeField("Completion Time", null=True, blank=True)
    validation_status = models.CharField("Validation Status", max_length=30, default="PENDING")
    input_payload = models.TextField("Structured Input Payload", blank=True, default="")
    output_payload = models.TextField("Structured Output Payload", blank=True, default="")
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


class SchedulingDecision(models.Model):
    """Detailed record of scheduler decision and resource evaluation rationale."""

    decision_id = models.CharField("Decision ID", max_length=60, unique=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="decisions")
    algorithm = models.CharField("Algorithm", max_length=50)
    selected_resource = models.CharField("Selected Resource", max_length=50)
    selected_tier = models.CharField("Selected Tier", max_length=30)
    objective_scores = models.TextField("Objective Scores JSON", blank=True)
    rejected_candidates = models.TextField("Rejected Candidates JSON", blank=True)
    decision_rationale = models.TextField("Decision Rationale", blank=True)
    timestamp = models.DateTimeField("Timestamp", default=timezone.now)

    class Meta:
        verbose_name = "Scheduling Decision"
        verbose_name_plural = "Scheduling Decisions"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.task.task_id} -> {self.selected_resource} ({self.algorithm})"


class ExperimentRun(models.Model):
    """Recorded benchmark experiment comparing GA against baselines."""

    experiment_id = models.CharField("Experiment ID", max_length=60, unique=True)
    name = models.CharField("Experiment Name", max_length=200)
    seed = models.IntegerField("Random Seed", default=42)
    tasks_count = models.IntegerField("Tasks Count", default=0)
    configuration_json = models.TextField("Configuration JSON", blank=True)
    results_json = models.TextField("Results JSON", blank=True)
    created_at = models.DateTimeField("Created At", default=timezone.now)

    class Meta:
        verbose_name = "Experiment Run"
        verbose_name_plural = "Experiment Runs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.experiment_id}: {self.name} ({self.tasks_count} tasks)"