from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register([
    RawFile, SpectromineQueue, SpectromineWorker, NoteFile, SsdStorage,
    HdStorage, RemoteStorage, OfflineStorage, PklStorage, MaxquantQueue,
    MaxquantWorker, MsfraggerQueue, MsfraggerWorker, PdQueue, PdWorker,
    UserProfile
])
