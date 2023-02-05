"""
Define the data tables that can be managed by Django admin site.
"""
from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register([
    FileStorage, SampleRecord, UserSettings, SystemSettings,
    WorkerStatus, DataAnalysisQueue, ProcessingApp, VisualizationApp
])
