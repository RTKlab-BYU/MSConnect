from operator import truediv
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.conf import settings
from rest_framework import generics
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db.models.functions.datetime import TruncMonth
from django.contrib.auth.models import Group
import plotly.graph_objs as go
from plotly.graph_objs import Scatter
from plotly.offline import plot

from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import get_user_model
from django.core.files import File
from django.urls import path, include

from django.conf import settings
from file_manager .models import ProcessingApp, VisualizationApp
from zipfile import ZipFile
import os


# app name, must be the same as in the database
appname = "PD"

# up initial installation or upgrading
installed_app_version = ProcessingApp.objects.filter(
    name=appname).first().version
attached_file_version_string = ProcessingApp.objects.filter(
    name=appname).first().install_package.name
attached_version = attached_file_version_string.split("ver")[1]

# only install from package if newer
if int(attached_version) > int(installed_app_version):
    print(f"upgrading {appname} from version {installed_app_version} "
          f"to {attached_version}")
    installaton_file = os.path.join(settings.MEDIA_ROOT,
                                    attached_file_version_string)
    if os.path.exists(installaton_file):
        print('Extracting all the files now...')
        archive = ZipFile(installaton_file)
        for file in archive.namelist():
            if file.endswith('.py'):
                archive.extract(file, 'file_manager/processing_apps')
            if file.endswith('.html'):
                archive.extract(file, 'file_manager/templates/filemanager')
        # TODO update database verion, need way to verify update sucessed
        ProcessingApp.objects.filter(
            name=appname).update(version=attached_version)


# app page
@ login_required
def view(request):
    args = {}

    return render(request, 'filemanager/pd.html', args)


urlpatterns = [path("processing/pd/", view, name='Proteomic Discoverer')]
