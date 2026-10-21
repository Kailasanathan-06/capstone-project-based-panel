"""Cloud - authentication helpers (service-account based)."""

from .google_drive_service import get_credentials, is_configured


def cloud_ready():
    """Boolean: are we in live-Drive mode or simulation mode?"""
    return is_configured()