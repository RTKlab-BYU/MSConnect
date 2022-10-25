from django.urls import path, include

from . import views
from django.conf.urls.static import static
from . import views
from django.conf import settings
from rest_framework import routers
import glob
import os

router = routers.DefaultRouter()
router.register(r'FileStorage', views.FileStorageViewSet)
router.register(r'SampleRecord', views.SampleRecordViewSet)
router.register(r'WorkerStatus', views.WorkerStatusViewSet)
router.register(r'DataAnalysisQueue', views.DataAnalysisQueueViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/', views.auth, name="Auth"),
    path('', views.dashboard, name='Dashboard'),
    path("records/", views.records, name='Records'),
    path("records/load/<int:pk>", views.load_record, name='Load_record'),
    path("records/sampleinfo/<int:pk>", views.sample_info, name='sample'),
    path("processing/", views.processing_center, name='Processing Center'),
    path("visualization/", views.visual_center, name='Visualization Center'),

    path("settings/", views.user_settings, name='Settings'),
    path("system_settings/", views.system_settings, name='system_settings'),

    path("help/", views.help, name='Help'),
    path("upload/", views.uploader, name='uploader'),  # test internal purpose



]

# import all sub_module for processing
# TODO might be security issues here
for entry in os.scandir('file_manager/processing_apps'):
    if entry.is_file():
        module_name = entry.name[:-3]
        string = f'from file_manager.processing_apps import {module_name}'
        exec(string)
        string2 = f'urlpatterns += {module_name}.urlpatterns'
        exec(string2)

'''

for entry in os.scandir('file_manager/visualization_apps'):
    if entry.is_file():
        module_name = entry.name[:-3]
        string = f'from file_manager.visualization_apps import {module_name}'
        exec(string)
        string2 = f'urlpatterns += {module_name}.urlpatterns'
        exec(string2)
'''
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
