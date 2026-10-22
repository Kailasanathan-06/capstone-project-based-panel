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