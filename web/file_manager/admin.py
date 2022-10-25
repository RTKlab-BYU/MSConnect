from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register([
    FileStorage, SampleRecord, UserSettings, SystemSettings,
    WorkerStatus, DataAnalysisQueue, Review,
    AppAuthor, ProcessingApp, VisualizationApp
])
