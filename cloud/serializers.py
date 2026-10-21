"""
Cloud - Serializers for Google Drive integration.
"""

from rest_framework import serializers
from .models import GoogleDriveFile, CloudFolder, CloudUploadRecord


class GoogleDriveFileSerializer(serializers.ModelSerializer):
    """Serializer for Google Drive file metadata."""

    class Meta:
        model = GoogleDriveFile
        fields = [
            "file_id", "file_name", "file_size", "upload_timestamp",
            "processing_status", "task", "mec_id", "folder_id",
            "folder_path", "mime_type", "result_type"
        ]


class CloudFolderSerializer(serializers.ModelSerializer):
    """Serializer for cloud folder structure."""

    class Meta:
        model = CloudFolder
        fields = ["id", "name", "folder_id", "parent_folder", "folder_path", "created_at"]


class CloudUploadRecordSerializer(serializers.ModelSerializer):
    """Serializer for upload records."""

    class Meta:
        model = CloudUploadRecord
        fields = [
            "task", "mec_id", "file_id", "file_size", "upload_start",
            "upload_end", "duration", "status", "error_message", "created_at"
        ]