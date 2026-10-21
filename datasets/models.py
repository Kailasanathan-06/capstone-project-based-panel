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