"""
Main URL configuration for SecureDT project.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views
from datasets import views_pages as page_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('register/', views.register, name='register'),

    # Essential Core Application Pages (A through G)
    path('', page_views.dashboard_view, name='dashboard'),
    path('upload/', page_views.upload_dataset_view, name='upload_dataset'),
    path('digital-twin/', page_views.digital_twin_view, name='digital_twin'),
    path('storage-allocation/', page_views.storage_allocation_view, name='storage_allocation'),
    path('reports/', page_views.dataset_reports_view, name='dataset_reports'),
    path('reports/<str:report_id>/', page_views.report_detail_view, name='report_detail'),
    path('reports/<str:report_id>/csv/', page_views.report_download_csv_view, name='report_download_csv'),
    path('tasks/', page_views.task_history_view, name='task_history'),

    # Core Application APIs
    path('api/app/dashboard-stats/', page_views.dashboard_api, name='api_dashboard_stats'),
    path('api/app/upload-zip/', page_views.upload_dataset_api, name='api_upload_dataset'),
    path('api/app/upload-demo-zip/', page_views.upload_demo_zip_api, name='api_upload_demo_zip'),
    path('api/app/digital-twin/', page_views.digital_twin_api, name='api_digital_twin_status'),
    path('api/app/storage-allocations/', page_views.storage_allocation_api, name='api_storage_allocations'),
    path('api/app/reports/', page_views.dataset_reports_api, name='api_dataset_reports'),
    path('api/app/reports/<str:report_id>/', page_views.report_detail_api, name='api_report_detail'),
    path('api/app/tasks/', page_views.task_history_api, name='api_task_history'),

    # Existing Modular Backend APIs
    path('api/', include('securedt.api_urls')),
    path('api/auth/', include('securedt.auth_urls')),
    path('api/mec/', include('mec_manager.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('api/cloud/', include('cloud.urls')),
    path('api/digital-twin/', include('digital_twin.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('datasets/app/', include('datasets.urls')),
    path('api/datasets/', include('datasets.urls')),
    path('medical-datasets/', include('datasets.urls')),
    
    # Legacy / Subsystem Views preserved for backward compatibility
    path('medical-dataset/', TemplateView.as_view(template_name='medical_dataset_explorer.html'), name='medical_dataset_explorer'),
    path('task-routing/', TemplateView.as_view(template_name='task_routing.html'), name='task_routing'),
    path('mec-infrastructure/', TemplateView.as_view(template_name='mec_infrastructure.html'), name='mec_infrastructure'),
    path('genetic-algorithm/', TemplateView.as_view(template_name='genetic_algorithm.html'), name='genetic_algorithm'),
    path('ai-intelligence/', TemplateView.as_view(template_name='ai_intelligence.html'), name='ai_intelligence'),
    path('security-monitor/', TemplateView.as_view(template_name='security_monitor.html'), name='security_monitor'),
    path('attack-simulation/', TemplateView.as_view(template_name='attack_simulation.html'), name='attack_simulation'),
    path('storage-attack/', TemplateView.as_view(template_name='storage_attack.html'), name='storage_attack'),
    path('datasets/', TemplateView.as_view(template_name='dataset_manager.html'), name='dataset_manager'),
    path('cloud-storage/', TemplateView.as_view(template_name='cloud_storage.html'), name='cloud_storage'),
    path('data-flow/', TemplateView.as_view(template_name='data_flow.html'), name='data_flow'),
    path('analytics/', TemplateView.as_view(template_name='analytics.html'), name='analytics'),
    path('performance/', TemplateView.as_view(template_name='performance.html'), name='performance'),
    path('energy-monitor/', TemplateView.as_view(template_name='energy_monitor.html'), name='energy_monitor'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)