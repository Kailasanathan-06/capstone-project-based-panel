from django.urls import path

from . import views

urlpatterns = [
    path("api/datasets/overview", views.dataset_overview, name="dataset_overview"),
    path("api/datasets/cards", views.dataset_cards, name="dataset_cards"),
    path("api/datasets/visualizations", views.dataset_visualizations, name="dataset_visualizations"),
    path("api/datasets/mysql", views.dataset_mysql_rows, name="dataset_mysql"),
    path("api/datasets/experiment-options", views.experiment_options, name="dataset_experiment_options"),
    path("api/datasets/verified-catalog", views.verified_catalog, name="verified_catalog"),
    path("api/datasets/verified-detail/<str:slug>", views.verified_detail, name="verified_detail"),
    # Medical Dataset Routes
    path("medical/", views.medical_dataset_explorer_view, name="medical_dataset_explorer"),
    path("medical/summary/", views.medical_dataset_summary, name="medical_dataset_summary"),
    path("medical/samples/", views.medical_dataset_samples, name="medical_dataset_samples"),
    path("medical/image/<str:sample_id>/", views.medical_dataset_sample_image, name="medical_dataset_sample_image"),
    path("medical/create-task/", views.medical_dataset_create_task, name="medical_dataset_create_task"),
    path("api/datasets/medical/summary/", views.medical_dataset_summary),
    path("api/datasets/medical/samples/", views.medical_dataset_samples),
    path("api/datasets/medical/image/<str:sample_id>/", views.medical_dataset_sample_image),
    path("api/datasets/medical/create-task/", views.medical_dataset_create_task),
    # Phase 6 Storage Management Routes
    path("storage/destinations/", views.storage_destinations_api, name="storage_destinations_api"),
    path("storage/replicas/", views.storage_replicas_api, name="storage_replicas_api"),
    path("storage/replicate/", views.trigger_replication_api, name="trigger_replication_api"),
    path("storage/export-csv/", views.storage_export_csv_api, name="storage_export_csv_api"),
    path("storage/verify/", views.verify_replicas_api, name="verify_replicas_api"),
    path("api/datasets/storage/destinations/", views.storage_destinations_api),
    path("api/datasets/storage/replicas/", views.storage_replicas_api),
    path("api/datasets/storage/replicate/", views.trigger_replication_api),
    path("api/datasets/storage/export-csv/", views.storage_export_csv_api),
    path("api/datasets/storage/verify/", views.verify_replicas_api),
]