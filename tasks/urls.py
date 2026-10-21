"""
Tasks API URLs.
"""

from django.urls import path
from .views import TaskViewSet

urlpatterns = [
    path("dispatch/", TaskViewSet.as_view({"post": "dispatch_tasks"}), name="task_dispatch"),
    path("<str:pk>/cancel/", TaskViewSet.as_view({"post": "cancel"}), name="task_cancel"),
    path("<str:pk>/complete/", TaskViewSet.as_view({"post": "complete"}), name="task_complete"),
    path("<str:pk>/fail/", TaskViewSet.as_view({"post": "fail"}), name="task_fail"),
    path("<str:pk>/", TaskViewSet.as_view({"get": "retrieve"}), name="task_detail"),
    path("", TaskViewSet.as_view({"get": "list", "post": "create"}), name="task_list_create"),
]