"""Cloud - file and folder listing (MySQL mirror + live Drive where available)."""

from .models import GoogleDriveFile, CloudFolder
from .google_drive_service import get_drive_service, get_root_folder_id


def list_metadata(result_type=None, limit=200):
    q = GoogleDriveFile.objects.all()
    if result_type:
        q = q.filter(result_type=result_type)
    return list(q[:limit])


def list_drive_files(folder_id=None, limit=100):
    """Live listing from Google Drive; [] when not configured."""
    service = get_drive_service()
    if service is None:
        return []
    folder_id = folder_id or get_root_folder_id()
    try:
        query = "trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        fields = "files(id,name,size,mimeType,createdTime,webViewLink)"
        if service._rootDescUrl:  # noqa: SLF001 - discovery available
            pass
        result = service.files().list(q=query, fields=fields, pageSize=limit).execute()
        return result.get("files", [])
    except Exception:  # noqa: BLE001
        return []


def ensure_base_folders():
    """Idempotently record the standard folder structure in MySQL."""
    names = [
        ("DATASETS", None),
        ("RESULTS", None),
        ("MODELS", None),
        ("TASK_RESULTS", None),
        ("SECURITY_LOGS", None),
        ("UPLOADS", None),
    ]
    for name, parent in names:
        CloudFolder.objects.get_or_create(
            name=name, defaults={"folder_id": f"DRIVE-{name}", "folder_path": name}
        )
    return CloudFolder.objects.all()