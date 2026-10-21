"""
Digital Twin API URLs.
"""

from django.urls import path
from .views import DigitalTwinViewSet

urlpatterns = [
    path("compare/", DigitalTwinViewSet.as_view({"get": "compare"}), name="digital_twin_compare"),
    path("resources/", DigitalTwinViewSet.as_view({"get": "resources"}), name="digital_twin_resources"),
    path("attack/", DigitalTwinViewSet.as_view({"post": "attack"}), name="digital_twin_attack"),
    path("mitigate/", DigitalTwinViewSet.as_view({"post": "mitigate"}), name="digital_twin_mitigate"),
    path("unquarantine/", DigitalTwinViewSet.as_view({"post": "unquarantine"}), name="digital_twin_unquarantine"),
    path("schedule/", DigitalTwinViewSet.as_view({"post": "schedule"}), name="digital_twin_schedule"),
    path("storage/status/", DigitalTwinViewSet.as_view({"get": "storage_status"}), name="digital_twin_storage_status"),
    path("storage/attack/", DigitalTwinViewSet.as_view({"post": "storage_attack"}), name="digital_twin_storage_attack"),
    path("storage/recover/", DigitalTwinViewSet.as_view({"post": "storage_recover"}), name="digital_twin_storage_recover"),
    path("security/", DigitalTwinViewSet.as_view({"get": "security"}), name="digital_twin_security"),
    path("", DigitalTwinViewSet.as_view({"get": "list"}), name="digital_twin"),
]