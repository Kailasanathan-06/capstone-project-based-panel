"""
Cloud - Google Drive service account bootstrap.

All Drive access flows through here. When no valid service-account file exists
(e.g. a clean install), the cloud module runs in SIMULATION mode: file metadata
is stored in MySQL only, so the UI keeps working without real credentials.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from google.oauth2 import service_account as _sa
    from googleapiclient.discovery import build as _build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False


def get_credentials():
    """Load service-account credentials from the configured JSON file."""
    if not GOOGLE_DRIVE_AVAILABLE:
        return None
    path = getattr(settings, "GOOGLE_SERVICE_ACCOUNT_FILE", "") or ""
    if not path:
        return None
    import os

    if not os.path.isfile(path):
        return None
    try:
        return _sa.Credentials.from_service_account_file(
            path, scopes=["https://www.googleapis.com/auth/drive"]
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Drive credentials load failed: %s", exc)
        return None


def get_drive_service():
    """Build and return a Drive service, or None (simulation mode)."""
    creds = get_credentials()
    if creds is None:
        return None
    try:
        return _build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Drive service build failed: %s", exc)
        return None


def is_configured():
    service = get_drive_service()
    return service is not None


def get_root_folder_id():
    return getattr(settings, "GOOGLE_DRIVE_FOLDER_ID", "") or ""