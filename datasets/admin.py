from django.contrib import admin

from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "dataset_type", "record_count", "file_size", "validation_status", "processing_status", "google_drive_file_id")
    list_filter = ("dataset_type", "validation_status", "processing_status")
    search_fields = ("name", "dataset_id", "source")