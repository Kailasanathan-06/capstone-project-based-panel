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
]