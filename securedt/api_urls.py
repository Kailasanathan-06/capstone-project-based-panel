"""
API URLs for the main project.
"""

from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import api_state, csrf_token

urlpatterns = [
    path('state/', api_state, name='api_state'),
    path('csrf/', csrf_token, name='api_csrf'),
    path('auth/token/', obtain_auth_token, name='api_token'),
]