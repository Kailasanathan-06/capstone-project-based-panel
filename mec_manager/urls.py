"""
MEC Manager API URLs.

These paths are included from `/api/mec/`, so they are deliberately bare:
  /api/mec/                  GET  list devices
  /api/mec/register/         POST one-time registration (pairing code)
  /api/mec/heartbeat/        POST authenticated heartbeat
  /api/mec/pairing-codes/    GET/POST generate & list pairing codes
  /api/mec/<id>/             GET  device detail
  /api/mec/<id>/revoke/      POST revoke device
  /api/mec/<id>/unrevoke/    POST un-revoke device
  /api/mec/<id>/next-task/   GET  pull next assigned task (MEC auth)
  /api/mec/<id>/report-result/ POST report task result (MEC auth)
"""

from django.urls import path
from .views import MECAgentViewSet, PairingCodeViewSet, MECHeartbeatViewSet, MECTaskEndpoint

urlpatterns = [
    path("connected/", MECAgentViewSet.as_view({"get": "connected_mec"}), name="mec_connected"),
    path("ping/", MECAgentViewSet.as_view({"post": "ping_gateway"}), name="mec_ping_gateway"),
    path("register/", MECAgentViewSet.as_view({"post": "register"}), name="mec_register"),
    path("heartbeat/", MECAgentViewSet.as_view({"post": "heartbeat"}), name="mec_heartbeat"),
    path("pairing-codes/", PairingCodeViewSet.as_view({"get": "list", "post": "create"}), name="pairing_codes"),
    path("pairing-codes/<str:code>/", PairingCodeViewSet.as_view({"get": "retrieve"}), name="pairing_code_detail"),
    path("heartbeats/", MECHeartbeatViewSet.as_view({"get": "list"}), name="heartbeat_list"),
    path("<str:pk>/next-task/", MECTaskEndpoint.as_view({"get": "next_task"}), name="mec_next_task"),
    path("<str:pk>/report-result/", MECTaskEndpoint.as_view({"post": "report_result"}), name="mec_report_result"),
    path("<str:pk>/revoke/", MECAgentViewSet.as_view({"post": "revoke"}), name="mec_revoke"),
    path("<str:pk>/unrevoke/", MECAgentViewSet.as_view({"post": "unrevoke"}), name="mec_unrevoke"),
    path("", MECAgentViewSet.as_view({"get": "list"}), name="mec_list"),
    path("<str:pk>/", MECAgentViewSet.as_view({"get": "retrieve"}), name="mec_detail"),
]