"""
Dataset metadata model.

Only METADATA is stored in MySQL - never the raw dataset rows.  Large
datasets live on local disk (datasets/) and optionally in Google Drive;
the Google Drive file id is stored here for retrieval.
"""

from django.db import models
from django.utils import timezone


class Dataset(models.Model):
    """Metadata record for one dataset used by the project."""

    DATASET_TYPES = [("attacked", "ATTACKED"), ("benign", "BENIGN"), ("mixed", "MIXED")]

    dataset_id = models.CharField("Dataset ID", max_length=100, unique=True)
    name = models.CharField("Name", max_length=200)
    dataset_type = models.CharField("Type", max_length=20, choices=DATASET_TYPES)
    source = models.CharField("Source", max_length=500)
    file_name = models.CharField("File Name", max_length=300, blank=True)
    file_size = models.BigIntegerField("File Size (bytes)", default=0)
    record_count = models.BigIntegerField("Record Count", default=0)
    format = models.CharField("Format", max_length=50, blank=True)
    storage_location = models.CharField("Storage Location", max_length=500, blank=True)
    google_drive_file_id = models.CharField("Google Drive File ID", max_length=200, blank=True)
    processing_status = models.CharField("Processing Status", max_length=50, default="pending")
    validation_status = models.CharField("Validation Status", max_length=50, default="pending")
    created_at = models.DateTimeField("Created At", default=timezone.now)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Dataset"
        verbose_name_plural = "Datasets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.dataset_type}]"

    def to_dict(self):
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "dataset_type": self.dataset_type,
            "source": self.source,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "record_count": self.record_count,
            "format": self.format,
            "storage_location": self.storage_location,
            "google_drive_file_id": self.google_drive_file_id,
            "processing_status": self.processing_status,
            "validation_status": self.validation_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def sync_from_pipeline(overview, cards):
    """Optionally sync pipeline data into MySQL metadata rows."""
    rows = {}
    for card in cards:
        rows[card["name"]] = card
    existing = {d.name: d for d in Dataset.objects.all()}
    for name, card in rows.items():
        ds = existing.get(name)
        if ds is None:
            Dataset.objects.create(
                dataset_id=name.lower().replace(" ", "_"),
                name=name,
                dataset_type="attacked" if card["type"] == "ATTACKED" else card["type"].lower(),
                source=card["source"],
                file_name=card.get("name", ""),
                file_size=int(card.get("size_mb", 0) * 1024 * 1024),
                record_count=card.get("records_local", 0),
                format=card.get("format", ""),
                storage_location="/",
                validation_status="local" if card["status"] == "LOCAL" else "manual_download_required",
                processing_status=card.get("processing_status", "raw_only"),
            )
        else:
            ds.record_count = card.get("records_local", ds.record_count or 0)
            ds.file_size = int(card.get("size_mb", 0) * 1024 * 1024) or ds.file_size
            ds.validation_status = "local" if card["status"] == "LOCAL" else "manual_download_required"
            ds.processing_status = card.get("processing_status", ds.processing_status)
            ds.save(update_fields=["record_count", "file_size", "validation_status", "processing_status", "updated_at"])


class MedicalDatasetMetadata(models.Model):
    """Metadata and provenance for medical image datasets (e.g. MedMNIST PneumoniaMNIST)."""

    dataset_flag = models.CharField("Dataset Flag", max_length=50, unique=True, default="pneumoniamnist")
    name = models.CharField("Name", max_length=200, default="PneumoniaMNIST (MedMNIST v3)")
    description = models.TextField("Description", blank=True)
    source_url = models.CharField(
        "Official Source URL",
        max_length=500,
        default="https://zenodo.org/records/10519652/files/pneumoniamnist.npz?download=1",
    )
    license_terms = models.CharField("License", max_length=100, default="CC BY 4.0")
    citation = models.TextField(
        "Citation",
        default="Yang et al., MedMNIST v2 - A large-scale lightweight benchmark for 2D and 3D biomedical image classification, Scientific Data, 2023.",
    )
    version = models.CharField("Version", max_length=20, default="3.0.2")
    is_downloaded = models.BooleanField("Downloaded", default=False)
    download_date = models.DateTimeField("Retrieval Date", null=True, blank=True)
    storage_path = models.CharField("Storage Path (outside public webroot)", max_length=500, blank=True)
    sample_count = models.IntegerField("Sample Count", default=0)
    train_count = models.IntegerField("Train Count", default=0)
    val_count = models.IntegerField("Validation Count", default=0)
    test_count = models.IntegerField("Test Count", default=0)
    image_dimensions = models.CharField("Native Image Dimensions", max_length=50, default="1x28x28")
    channel_count = models.IntegerField("Channels", default=1)
    file_size_bytes = models.BigIntegerField("File Size (bytes)", default=0)
    created_at = models.DateTimeField("Created At", default=timezone.now)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Medical Dataset Metadata"
        verbose_name_plural = "Medical Dataset Metadata"

    def __str__(self):
        return f"{self.name} [{'DOWNLOADED' if self.is_downloaded else 'NOT DOWNLOADED'}]"


class MedicalDatasetSample(models.Model):
    """Synthetic medical image sample for browsing and task generation."""

    sample_id = models.CharField("Sample ID", max_length=100, unique=True)
    dataset = models.ForeignKey(MedicalDatasetMetadata, on_delete=models.CASCADE, related_name="samples")
    split = models.CharField(
        "Split",
        max_length=20,
        choices=[("train", "Train"), ("val", "Validation"), ("test", "Test")],
    )
    label_index = models.IntegerField("Label Index", default=0)
    label_name = models.CharField("Class Label", max_length=50, default="normal")
    relative_image_path = models.CharField("Relative Image Path", max_length=500)
    file_size_bytes = models.IntegerField("File Size (bytes)", default=0)
    image_format = models.CharField("Image Format", max_length=20, default="PNG")
    dimensions = models.CharField("Dimensions", max_length=30, default="28x28")
    sha256_checksum = models.CharField("SHA-256 Checksum", max_length=64, blank=True)
    processing_status = models.CharField("Processing Status", max_length=30, default="UNPROCESSED")
    created_at = models.DateTimeField("Created At", default=timezone.now)

    class Meta:
        verbose_name = "Medical Dataset Sample"
        verbose_name_plural = "Medical Dataset Samples"
        ordering = ["split", "sample_id"]

    def __str__(self):
        return f"{self.sample_id} ({self.split} - {self.label_name})"


class WorkloadScenario(models.Model):
    """Definition and test fixture metadata for the 14 hospital workload scenarios."""

    CATEGORY_CHOICES = [
        ("SUCCESS", "Success Datasets"),
        ("ERROR", "Error Datasets"),
        ("SECURITY", "Hacked / Security Event Datasets"),
        ("TIMEOUT", "Looping / Timeout Datasets"),
    ]

    scenario_id = models.CharField("Scenario ID", max_length=60, unique=True)
    name = models.CharField("Name", max_length=200)
    category = models.CharField("Category", max_length=30, choices=CATEGORY_CHOICES)
    workload_type = models.CharField("Workload Type", max_length=60)
    description = models.TextField("Description", blank=True)
    input_format = models.CharField("Input Format", max_length=30, default="JSON")
    input_size_bytes = models.BigIntegerField("Input Size (bytes)", default=0)
    input_file_path = models.CharField("Input File Path", max_length=500, blank=True)
    input_payload = models.TextField("Structured Input Payload", blank=True)
    processing_requirements = models.TextField("Processing Requirements", blank=True)
    expected_status = models.CharField("Expected Status", max_length=30, default="COMPLETED")
    expected_result_description = models.TextField("Expected Result", blank=True)
    validation_rules = models.TextField("Validation Rules", blank=True)
    privacy_policy = models.CharField("Privacy Policy", max_length=30, default="TRUSTED_EDGE")
    cpu_cycles_giga = models.FloatField("CPU Cycles (Giga)", default=0.5)
    memory_mb = models.IntegerField("Memory (MB)", default=512)
    deadline_ms = models.IntegerField("Deadline (ms)", default=500)
    privacy_sensitivity = models.FloatField("Privacy Sensitivity", default=0.5)
    security_sensitivity = models.FloatField("Security Sensitivity", default=0.1)
    timeout_seconds = models.IntegerField("Timeout Seconds", default=60)
    max_retries = models.IntegerField("Max Retries", default=3)
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Created At", default=timezone.now)

    class Meta:
        verbose_name = "Workload Scenario"
        verbose_name_plural = "Workload Scenarios"
        ordering = ["category", "scenario_id"]

    def __str__(self):
        return f"{self.scenario_id}: {self.name} [{self.category}]"

    def to_dict(self):
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "category": self.category,
            "workload_type": self.workload_type,
            "description": self.description,
            "input_format": self.input_format,
            "input_size_bytes": self.input_size_bytes,
            "input_file_path": self.input_file_path,
            "expected_status": self.expected_status,
            "privacy_policy": self.privacy_policy,
            "cpu_cycles_giga": self.cpu_cycles_giga,
            "memory_mb": self.memory_mb,
            "deadline_ms": self.deadline_ms,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }


class DatasetVersion(models.Model):
    """Version metadata for registered public or synthetic datasets."""

    version_tag = models.CharField("Version Tag", max_length=50)
    dataset_name = models.CharField("Dataset Name", max_length=200)
    dataset_flag = models.CharField("Dataset Flag", max_length=50, blank=True)
    sha256_checksum = models.CharField("SHA-256 Checksum", max_length=64, blank=True)
    total_samples = models.IntegerField("Total Samples", default=0)
    train_samples = models.IntegerField("Train Samples", default=0)
    val_samples = models.IntegerField("Validation Samples", default=0)
    test_samples = models.IntegerField("Test Samples", default=0)
    license = models.CharField("License", max_length=100, default="CC BY 4.0")
    source_url = models.CharField("Source URL", max_length=500, blank=True)
    storage_path = models.CharField("Storage Path", max_length=500, blank=True)
    is_verified = models.BooleanField("Verified", default=False)
    created_at = models.DateTimeField("Created At", default=timezone.now)

    class Meta:
        verbose_name = "Dataset Version"
        verbose_name_plural = "Dataset Versions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.dataset_name} ({self.version_tag})"


class StorageDestination(models.Model):
    """Configured edge-cloud storage destination (Local, MEC, Cloud)."""

    DESTINATION_TYPES = [
        ("LOCAL", "Hospital / Local Storage"),
        ("MEC", "Authorized Edge Node Storage"),
        ("CLOUD", "Cloud Storage / Emulator"),
    ]

    destination_id = models.CharField("Destination ID", max_length=50, unique=True)
    name = models.CharField("Name", max_length=100)
    destination_type = models.CharField("Destination Type", max_length=30, choices=DESTINATION_TYPES)
    base_path = models.CharField("Base Filesystem Path", max_length=500)
    is_active = models.BooleanField("Active", default=True)
    is_emulator = models.BooleanField("Is Emulator / Local Cloud Stub", default=False)
    capacity_bytes = models.BigIntegerField("Capacity (Bytes)", default=107374182400)
    used_bytes = models.BigIntegerField("Used (Bytes)", default=0)
    privacy_tier_allowed = models.CharField("Max Allowed Privacy Policy", max_length=30, default="CLOUD_ALLOWED")
    created_at = models.DateTimeField("Created At", default=timezone.now)

    class Meta:
        verbose_name = "Storage Destination"
        verbose_name_plural = "Storage Destinations"
        ordering = ["destination_id"]

    def __str__(self):
        return f"{self.destination_id} ({self.destination_type})"


class DatasetStorageReplica(models.Model):
    """Tracks physical file/object replica in a storage destination with verification."""

    REPLICATION_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COPYING", "Copying"),
        ("VERIFIED", "Verified"),
        ("FAILED", "Failed"),
        ("BLOCKED_BY_POLICY", "Blocked by Policy"),
        ("UNAVAILABLE", "Unavailable"),
    ]

    replica_id = models.CharField("Replica ID", max_length=60, unique=True)
    dataset_id = models.CharField("Dataset ID", max_length=100)
    scenario = models.ForeignKey(WorkloadScenario, null=True, blank=True, on_delete=models.SET_NULL, related_name="replicas")
    storage_destination = models.ForeignKey(StorageDestination, on_delete=models.CASCADE, related_name="replicas")
    relative_key = models.CharField("Relative Object Key", max_length=500)
    absolute_path = models.CharField("Absolute Path", max_length=500)
    file_size_bytes = models.BigIntegerField("File Size (bytes)", default=0)
    sha256_checksum = models.CharField("SHA-256 Checksum", max_length=64, blank=True)
    replication_status = models.CharField("Replication Status", max_length=30, default="PENDING", choices=REPLICATION_STATUS_CHOICES)
    replication_job_id = models.CharField("Replication Job ID", max_length=60, blank=True)
    last_error = models.TextField("Last Error", blank=True)
    is_available = models.BooleanField("Available", default=True)
    created_at = models.DateTimeField("Created At", default=timezone.now)
    last_verified_at = models.DateTimeField("Last Verified At", null=True, blank=True)

    class Meta:
        verbose_name = "Dataset Storage Replica"
        verbose_name_plural = "Dataset Storage Replicas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.dataset_id} @ {self.storage_destination.destination_id} [{self.replication_status}]"


class SecurityAuditEvent(models.Model):
    """Persistent audit log of defensive security and policy enforcement events."""

    SEVERITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]

    event_id = models.CharField("Event ID", max_length=50, unique=True)
    event_type = models.CharField("Event Type", max_length=60)
    severity = models.CharField("Severity", max_length=20, default="HIGH", choices=SEVERITY_CHOICES)
    task_id = models.CharField("Task ID", max_length=50, blank=True)
    device_id = models.CharField("Device ID", max_length=50, blank=True)
    source_ip = models.CharField("Source IP", max_length=50, blank=True)
    description = models.TextField("Description")
    details_json = models.TextField("Details JSON (No plaintext secrets)", blank=True)
    blocked = models.BooleanField("Blocked / Defended", default=True)
    timestamp = models.DateTimeField("Timestamp", default=timezone.now)

    class Meta:
        verbose_name = "Security Audit Event"
        verbose_name_plural = "Security Audit Events"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.severity}] {self.event_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class DatasetUpload(models.Model):
    """Tracks uploaded ZIP archives and processing lifecycle."""

    EXECUTION_MODES = [
        ("SIMULATION", "Simulation Mode"),
        ("EXECUTION", "Execution Mode"),
    ]

    STATUS_CHOICES = [
        ("RECEIVED", "Received"),
        ("VALIDATING", "Validating"),
        ("INVENTORIED", "Inventoried"),
        ("ANALYZING", "Analyzing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    upload_id = models.CharField("Upload ID", max_length=60, unique=True)
    file_name = models.CharField("Archive File Name", max_length=255)
    file_size = models.BigIntegerField("File Size (bytes)", default=0)
    sha256_checksum = models.CharField("SHA-256 Checksum", max_length=64, blank=True)
    archive_type = models.CharField("Archive Type", max_length=20, default="ZIP")
    status = models.CharField("Status", max_length=30, default="RECEIVED", choices=STATUS_CHOICES)
    total_files_count = models.IntegerField("Discovered Files Count", default=0)
    total_uncompressed_bytes = models.BigIntegerField("Total Uncompressed Size", default=0)
    execution_mode = models.CharField("Execution Mode", max_length=20, default="SIMULATION", choices=EXECUTION_MODES)
    uploaded_at = models.DateTimeField("Uploaded At", default=timezone.now)
    error_message = models.TextField("Error Message", blank=True)

    class Meta:
        verbose_name = "Dataset Upload"
        verbose_name_plural = "Dataset Uploads"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.upload_id} - {self.file_name} [{self.status}]"


class DatasetInventoryItem(models.Model):
    """Individual dataset or file discovered inside an uploaded archive."""

    upload = models.ForeignKey(DatasetUpload, on_delete=models.CASCADE, related_name="inventory_items")
    file_name = models.CharField("File Name", max_length=255)
    relative_path = models.CharField("Relative Path in ZIP", max_length=500)
    file_size = models.BigIntegerField("Size (bytes)", default=0)
    format = models.CharField("Format", max_length=50, blank=True)
    detected_category = models.CharField("Detected Category", max_length=100, blank=True)
    declared_source = models.CharField("Declared Source Device", max_length=50, blank=True)
    privacy_policy = models.CharField("Privacy Policy", max_length=50, default="TRUSTED_EDGE")
    local_eligible = models.BooleanField("Local Eligible", default=True)
    mec_eligible = models.BooleanField("MEC/Edge Eligible", default=True)
    cloud_eligible = models.BooleanField("Cloud Eligible", default=True)
    selected_destination = models.CharField("Selected Destination", max_length=50, default="UNASSIGNED")
    decision_rationale = models.TextField("Decision Rationale", blank=True)
    rejected_destinations_json = models.TextField("Rejected Destinations JSON", blank=True)
    status = models.CharField("Status", max_length=40, default="RECOMMENDED")
    sha256_checksum = models.CharField("SHA-256 Checksum", max_length=64, blank=True)
    error_message = models.TextField("Error Message", blank=True)

    class Meta:
        verbose_name = "Dataset Inventory Item"
        verbose_name_plural = "Dataset Inventory Items"
        ordering = ["upload", "relative_path"]

    def __str__(self):
        return f"{self.file_name} -> {self.selected_destination} [{self.status}]"


class DatasetAnalysisReport(models.Model):
    """Persistent dataset storage and task allocation report."""

    report_id = models.CharField("Report ID", max_length=60, unique=True)
    upload = models.OneToOneField(DatasetUpload, on_delete=models.CASCADE, related_name="report")
    title = models.CharField("Report Title", max_length=255)
    method_used = models.CharField("Analysis Method Used", max_length=100, default="Genetic Algorithm & Policy Constraints Engine")
    analysis_duration_ms = models.FloatField("Analysis Duration (ms)", default=0.0)
    scheduling_duration_ms = models.FloatField("Scheduling Duration (ms)", default=0.0)
    summary_json = models.TextField("Summary JSON", blank=True)
    inventory_json = models.TextField("Inventory JSON", blank=True)
    ai_analysis_json = models.TextField("AI Analysis JSON", blank=True)
    allocation_json = models.TextField("Allocation JSON", blank=True)
    security_audit_json = models.TextField("Security Audit JSON", blank=True)
    final_result_json = models.TextField("Final Result JSON", blank=True)
    created_at = models.DateTimeField("Created At", default=timezone.now)

    class Meta:
        verbose_name = "Dataset Analysis Report"
        verbose_name_plural = "Dataset Analysis Reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_id} - {self.title}"