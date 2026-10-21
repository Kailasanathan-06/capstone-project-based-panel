"""Cloud - file download from Google Drive with metadata fallback."""

import io
import logging

from rest_framework.response import Response

from .models import GoogleDriveFile
from .google_drive_service import get_drive_service

logger = logging.getLogger(__name__)


def download_metadata(file_id):
    """Return the MySQL metadata row for a file."""
    try:
        return GoogleDriveFile.objects.get(file_id=file_id)
    except GoogleDriveFile.DoesNotExist:
        return None


def stream_download(file_id):
    """
    Download a file's bytes from Google Drive.
    Returns (content_bytes, mime_type, file_name) or (None, None, None).
    """
    service = get_drive_service()
    metadata = download_metadata(file_id)
    if service is None:
        return None, None, None
    try:
        if metadata is None:
            meta = service.files().get(fileId=file_id, fields="name,mimeType").execute()
            file_name = meta.get("name", file_id)
            mime_type = meta.get("mimeType", "application/octet-stream")
        else:
            file_name = metadata.file_name
            mime_type = metadata.mime_type or "application/octet-stream"
        buf = io.BytesIO()
        from googleapiclient.http import MediaIoBaseDownload

        downloader = MediaIoBaseDownload(
            service.files().get_media(fileId=file_id), buf, chunksize=1024 * 1024
        )
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue(), mime_type, file_name
    except Exception as exc:  # noqa: BLE001
        logger.warning("Drive download failed: %s", exc)
        return None, None, None