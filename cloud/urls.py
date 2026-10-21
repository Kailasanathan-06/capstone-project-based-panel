"""
Cloud API URLs.
"""

from django.urls import path
from .views import CloudFileViewSet, CloudFolderViewSet, CloudUploadRecordViewSet

urlpatterns = [
    path("files/", CloudFileViewSet.as_view({"get": "list", "post": "create"}), name="cloud_files"),
    path("upload/", CloudFileViewSet.as_view({"post": "create"}), name="cloud_upload"),
    path("download/<str:file_id>/", CloudFileViewSet.as_view({"get": "download"}), name="cloud_download"),
    path("status/", CloudFileViewSet.as_view({"get": "status"}), name="cloud_status"),
    path("folders/", CloudFolderViewSet.as_view({"get": "list", "post": "create"}), name="cloud_folders"),
    path("upload-records/", CloudUploadRecordViewSet.as_view({"get": "list"}), name="cloud_upload_records"),
]