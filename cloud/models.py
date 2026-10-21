"""
Cloud - Google Drive integration module.

Handles file upload/download, folder creation, metadata retrieval, and result/dataset storage.
All Google Drive operations go through the Django API, never directly from MEC agents.
"""

from django.conf import settings
from django.db import models


class GoogleDriveFile(models.Model):
    """Metadata for files stored in Google Drive."""

    # Google Drive file ID
    file_id = models.CharField("Google Drive File ID", max_length=200, unique=True)
    # Original file name
    file_name = models.CharField("File Name", max_length=500)
    # File size in bytes
    file_size = models.BigIntegerField("File Size (bytes)")
    # Upload timestamp
    upload_timestamp = models.DateTimeField("Upload Timestamp")
    # Processing status
    processing_status = models.CharField(
        "Processing Status", max_length=50, default="pending"
    )
    # Associated task ID
    task = models.CharField("Task ID", max_length=50, blank=True)
    # Associated MEC ID
    mec_id = models.CharField("MEC ID", max_length=20, blank=True)
    # Google Drive folder ID where file is stored
    folder_id = models.CharField("Folder ID", max_length=200)
    # Folder path within the project structure
    folder_path = models.CharField("Folder Path", max_length=500, default="")
    # MIME type
    mime_type = models.CharField("MIME Type", max_length=200, blank=True)
    # Result type: "dataset", "result", "model", "pcap"
    result_type = models.CharField("Result Type", max_length=50, default="result")

    class Meta:
        verbose_name = "Google Drive File"
        verbose_name_plural = "Google Drive Files"
        ordering = ["-upload_timestamp"]

    def __str__(self):
        return f"{self.file_name} ({self.get_result_type_display()})"


class CloudFolder(models.Model):
    """Google Drive folder structure for the project."""

    # Folder name
    name = models.CharField("Folder Name", max_length=200)
    # Google Drive folder ID
    folder_id = models.CharField("Google Drive Folder ID", max_length=200, unique=True)
    # Parent folder
    parent_folder = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="sub_folders"
    )
    # Folder path from root
    folder_path = models.CharField("Folder Path", max_length=500)
    # Creation timestamp
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        verbose_name = "Cloud Folder"
        verbose_name_plural = "Cloud Folders"
        ordering = ["folder_path"]

    def __str__(self):
        return self.name


class CloudUploadRecord(models.Model):
    """Record of upload operations for auditing."""

    # Associated task
    task = models.CharField("Task ID", max_length=50, blank=True)
    # MEC ID that uploaded
    mec_id = models.CharField("MEC ID", max_length=20, blank=True)
    # Google Drive file ID
    file_id = models.CharField("Google Drive File ID", max_length=200)
    # File size
    file_size = models.BigIntegerField("File Size (bytes)")
    # Upload start time
    upload_start = models.DateTimeField("Upload Start")
    # Upload end time
    upload_end = models.DateTimeField("Upload End")
    # Duration in seconds
    duration = models.FloatField("Duration (seconds)")
    # Status: SUCCESS, FAILED, PARTIAL
    status = models.CharField("Status", max_length=20, default="PENDING")
    # Error message if failed
    error_message = models.TextField("Error Message", blank=True)
    # Created at
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        verbose_name = "Cloud Upload Record"
        verbose_name_plural = "Cloud Upload Records"

    def __str__(self):
        return f"Upload {self.file_id}: {self.status}"