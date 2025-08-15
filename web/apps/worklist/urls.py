from django.urls import path
from . import views

urlpatterns = [
    path('', views.worklist_view, name='worklist'),
    path('template/', views.download_template_excel, name='download_template_excel'),
    path('download/<str:which>/', views.download_csv, name='download_csv'),
]
