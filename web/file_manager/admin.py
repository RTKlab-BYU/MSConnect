from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register([
    FileStorage, SampleRecord, UserSettings, SystemSettings,
<<<<<<< HEAD
    WorkerStatus, DataAnalysisQueue, Review,
    AppAuthor, ProcessingApp, VisualizationApp
=======
    WorkerStatus, DataAnalysisQueue, ProcessingApp, VisualizationApp
>>>>>>> adding_process_node
])
