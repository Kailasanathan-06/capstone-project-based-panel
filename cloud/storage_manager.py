"""Cloud - storage layer combining Google Drive + MySQL metadata."""

from .google_drive_service import is_configured, get_root_folder_id
from .authentication import cloud_ready
from .upload import upload_bytes
from .download import download_metadata, stream_download
from .file_manager import list_metadata, list_drive_files, ensure_base_folders


class StorageManager:
    """High-level cloud storage operations used by views and MEC reports."""

    def __init__(self):
        self.configured = is_configured()
        self.mode = "GOOGLE_DRIVE" if self.configured else "SIMULATION"
        self.root_folder_id = get_root_folder_id()

    def status(self):
        folders = ensure_base_folders()
        files = list_metadata()
        return {
            "mode": self.mode,
            "configured": is_configured(),
            "root_folder_id": self.root_folder_id,
            "folders": [f.folder_path for f in folders],
            "total_files": len(files),
            "drive_files": len(list_drive_files()),
        }

    def upload(self, file_name, file_bytes, mime_type="application/octet-stream",
               result_type="result", task="", mec_id=""):
        return upload_bytes(
            file_name, file_bytes, mime_type=mime_type,
            result_type=result_type, task=task, mec_id=mec_id,
        )

    def download(self, file_id):
        return stream_download(file_id) or (None, None, None), download_metadata(file_id)

    def list_files(self, result_type=None):
        return list_metadata(result_type=result_type)