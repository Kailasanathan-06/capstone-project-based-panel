"""
Analytics API URLs.
"""

from django.urls import path
from .views import AnalyticsViewSet

urlpatterns = [
    path("overview/", AnalyticsViewSet.as_view({"get": "overview"}), name="analytics_overview"),
    path("mec-metrics/", AnalyticsViewSet.as_view({"get": "mec_metrics"}), name="analytics_mec_metrics"),
    path("task-metrics/", AnalyticsViewSet.as_view({"get": "task_metrics"}), name="analytics_task_metrics"),
    path("energy-metrics/", AnalyticsViewSet.as_view({"get": "energy_metrics"}), name="analytics_energy"),
    path("security-metrics/", AnalyticsViewSet.as_view({"get": "security_metrics"}), name="analytics_security"),
    path("cloud-metrics/", AnalyticsViewSet.as_view({"get": "cloud_metrics"}), name="analytics_cloud"),
    path("history/", AnalyticsViewSet.as_view({"get": "history"}), name="analytics_history"),
    path("ai-status/", AnalyticsViewSet.as_view({"get": "ai_status", "post": "ai_status"}), name="analytics_ai_status"),
    path("benchmark/", AnalyticsViewSet.as_view({"get": "benchmark"}), name="analytics_benchmark"),
    path("data-flow/", AnalyticsViewSet.as_view({"get": "data_flow"}), name="analytics_data_flow"),
]