"""Cloud - file upload to Google Drive (with MySQL metadata mirror)."""

import io
import base64
import logging

from django.utils import timezone

from .models import GoogleDriveFile, CloudUploadRecord
from .google_drive_service import get_drive_service, get_root_folder_id

logger = logging.getLogger(__name__)


def upload_bytes(file_name, file_bytes, mime_type="application/octet-stream",
                 result_type="result", task="", mec_id="", folder_id=""):
    """
    Upload raw bytes to Google Drive and record metadata in MySQL.
    Returns (record_file_ids:dict, error:str|None).
    In simulation mode only the MySQL metadata is recorded.
    """
    service = get_drive_service()
    folder_id = folder_id or get_root_folder_id()
    file_id = ""
    drive_uploaded = False

    if service is not None:
        try:
            from googleapiclient.http import MediaIoBaseUpload
            metadata = {"name": file_name, "mimeType": mime_type}
            if folder_id:
                metadata["parents"] = [folder_id]
            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)
            created = (
                service.files()
                .create(body=metadata, media_body=media, fields="id,name,size,mimeType,webViewLink")
                .execute()
            )
            file_id = created.get("id", "")
            file_size = int(created.get("size", 0)) if created.get("size") else len(file_bytes)
            drive_uploaded = True
            folder_path = folder_id or "SIMULATION"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Drive upload failed (%s); falling back to metadata-only", exc)
            file_id = ""
            file_size = len(file_bytes)
            folder_path = folder_id or "SIMULATION"

    else:
        file_id = "SIM-" + base64.urlsafe_b64encode(file_name.encode())[:12].decode()
        file_size = len(file_bytes)
        folder_path = folder_id or "SIMULATION"

    record, _ = GoogleDriveFile.objects.get_or_create(
        file_id=file_id or file_name,
        defaults={
            "file_name": file_name,
            "file_size": file_size,
            "upload_timestamp": timezone.now(),
            "processing_status": "completed",
            "task": task,
            "mec_id": mec_id,
            "folder_id": folder_id,
            "folder_path": folder_path,
            "mime_type": mime_type,
            "result_type": result_type,
        },
    )
    CloudUploadRecord.objects.create(
        task=task,
        mec_id=mec_id,
        file_id=record.file_id,
        file_size=file_size,
        upload_start=timezone.now(),
        upload_end=timezone.now(),
        duration=0.0,
        status="SUCCESS",
    )
    return {"file_id": record.file_id, "file_size": file_size, "drive_uploaded": drive_uploaded}, None