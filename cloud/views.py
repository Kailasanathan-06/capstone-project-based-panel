"""
Cloud - REST API Views (Google Drive via Django API).

Endpoints:
- GET  /api/cloud/files/            list metadata (MySQL) + live Drive files
- POST /api/cloud/upload/           multipart file upload
- GET  /api/cloud/download/<id>/    stream a file from Drive (or metadata)
- GET  /api/cloud/status/           cloud connection + storage status
- GET  /api/cloud/folders/          folder structure in MySQL
"""

import base64
import logging

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from .models import GoogleDriveFile, CloudFolder, CloudUploadRecord
from .serializers import GoogleDriveFileSerializer, CloudFolderSerializer, CloudUploadRecordSerializer
from .storage_manager import StorageManager
from .download import stream_download
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class CloudFileViewSet(viewsets.ViewSet):
    """Cloud file listing and upload."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if getattr(self, "action", None) in ("list", "status", "download"):
            return [AllowAny()]
        return super().get_permissions()

    def list(self, request):
        manager = StorageManager()
        result_type = request.query_params.get("result_type")
        metadata = GoogleDriveFileSerializer(
            GoogleDriveFile.objects.filter(processing_status__in=["completed", "pending"]), many=True
        ).data
        if result_type:
            filtered = [f for f in metadata if not result_type or f.get("result_type") == result_type]
        else:
            filtered = metadata
        return Response(
            {
                "mode": manager.mode,
                "configured": manager.configured,
                "files": filtered,
                "drive_files": GoogleDriveFileSerializer(manager.list_files(), many=True).data,
            }
        )

    def create(self, request):
        """Upload a file (multipart `file` or base64 `file_data`)."""
        manager = StorageManager()

        uploaded = request.FILES.get("file")
        if uploaded:
            file_name = uploaded.name
            file_bytes = uploaded.read()
            mime_type = uploaded.content_type or "application/octet-stream"
        else:
            file_name = request.data.get("file_name", "")
            file_bytes = base64.b64decode(request.data.get("file_data", ""))
            mime_type = request.data.get("mime_type", "application/octet-stream")

        if not file_name:
            return Response({"error": "file_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        result_type = request.data.get("result_type", "result")
        task = request.data.get("task", "")
        mec_id = request.data.get("mec_id", "")
        result, error = manager.upload(
            file_name,
            file_bytes,
            mime_type=mime_type,
            result_type=result_type,
            task=task,
            mec_id=mec_id,
        )
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(result, status=status.HTTP_201_CREATED)

    def download(self, request, file_id=None):
        """Stream the file bytes from Drive; otherwise return metadata only."""
        content, mime, name = stream_download(file_id)
        if content is not None:
            response = HttpResponse(content, content_type=mime or "application/octet-stream")
            response["Content-Disposition"] = f'attachment; filename="{name}"'
            return response
        try:
            meta = GoogleDriveFile.objects.get(file_id=file_id)
        except GoogleDriveFile.DoesNotExist:
            return Response({"error": "File not found"}, status=404)
        return Response(
            {
                "file_id": meta.file_id,
                "file_name": meta.file_name,
                "file_size": meta.file_size,
                "mode": "SIMULATION",
                "note": "Drive not configured; showing metadata only. Attach a service account to download real bytes.",
            }
        )

    def status(self, request):
        return Response(StorageManager().status())


class CloudFolderViewSet(viewsets.ViewSet):
    """Cloud folder management."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if getattr(self, "action", None) in ("list",):
            return [AllowAny()]
        return super().get_permissions()

    def list(self, request):
        from .file_manager import ensure_base_folders
        ensure_base_folders()
        return Response(CloudFolderSerializer(CloudFolder.objects.all(), many=True).data)

    def create(self, request):
        name = request.data.get("name", "").strip().upper() or "UPLOADS"
        folder, created = CloudFolder.objects.get_or_create(
            name=name, defaults={"folder_id": f"DRIVE-{name}", "folder_path": name}
        )
        return Response(CloudFolderSerializer(folder).data, status=status.HTTP_201_CREATED)


class CloudUploadRecordViewSet(viewsets.ViewSet):
    """Upload audit trail."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if getattr(self, "action", None) in ("list",):
            return [AllowAny()]
        return super().get_permissions()

    def list(self, request):
        records = CloudUploadRecord.objects.order_by("-created_at")[:100]
        return Response(CloudUploadRecordSerializer(records, many=True).data)