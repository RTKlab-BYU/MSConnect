"""
Define url rounting.
"""
# Standard library imports
import logging

# Django imports
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

# Django REST Framework imports
from rest_framework import routers

# Local imports
from .models import ProcessingApp, VisualizationApp
from . import views


logger = logging.getLogger(__name__)

# Wire up our API using automatic URL routing.
router = routers.DefaultRouter()
router.register(r'Users', views.UserListViewSet)
router.register(r'FileStorage', views.FileStorageViewSet)
router.register(r'SampleRecord', views.SampleRecordViewSet)
router.register(r'WorkerStatus', views.WorkerStatusViewSet)
router.register(r'DataAnalysisQueue', views.DataAnalysisQueueViewSet)
router.register(r'ProcessingApp', views.ProcessingAppViewset)

# Wire up URL routing for pages.
urlpatterns = [
    path('api/auth/', views.auth, name="Auth"),
    path('api/', include(router.urls)),
    path('', views.dashboard, name='Dashboard'),
    path("records/", views.records, name='Records'),
    path("records/load/<int:pk>", views.load_record, name='Load_record'),
    path("records/sampleinfo/<int:pk>", views.sample_info, name='sample'),
    # path("api/DataAnalysisQueue/<int:pk>",
    #      views.ProcessingAppViewset, name='sample'),
    path("processing/", views.processing_center, name='Processing Center'),
    path("visualization/", views.visual_center, name='Visualization Center'),
    path("app_center/", views.app_center, name='App_center'),
    path("settings/", views.user_settings, name='Settings'),
    path("system_settings/", views.system_settings, name='system_settings'),
    path("help/", views.help, name='Help'),
    path("upload/", views.uploader, name='uploader'),  # test purpose
    path('logs/', include('log_viewer.urls')),
]

###################################################
# used to import and adding url routing for processing and visualization apps
# have to comment out this section for makemigration work due to it uses models
# TODO might be security issues here, only allow admin to upload

for app in ProcessingApp.objects.filter(is_installed=True):
    try:
        module_name = app.program_file_name
        string = f'from file_manager.processing_apps import {module_name}'
        exec(string)
        string2 = f'urlpatterns += [path("processing/{app.UUID}/", ' \
            f'{module_name}.view, name="{app.name}")]'
        exec(string2)
    except Exception as err:
        logger.error(f"Process app {module_name} failed to load {err}")

for app in VisualizationApp.objects.filter(is_installed=True):
    try:
        module_name = app.program_file_name
        string = f'from file_manager.visualization_apps import {module_name}'
        exec(string)
        string2 = f'urlpatterns += [path("visual/{app.UUID}/", ' \
            f'{module_name}.view, name="{app.name}")]'
        exec(string2)
    except Exception as err:
        logger.error(f"Visualization app {module_name} failed to load {err}")
###########################################
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
