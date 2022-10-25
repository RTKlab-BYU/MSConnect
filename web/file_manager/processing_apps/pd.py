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
from file_manager .models import FileStorage, SampleRecord, UserSettings, SystemSettings, \
    WorkerStatus, DataAnalysisQueue, Review, \
    AppAuthor, ProcessingApp, VisualizationApp
from zipfile import ZipFile
import os

# app name, must be the same as in the database
appname = "PD"

# up initial installation or upgrading
installed_app_version = float(ProcessingApp.objects.filter(
    name=appname).first().version)
attached_file_version_string = ProcessingApp.objects.filter(
    name=appname).first().install_package.name
try:

    attached_version = float(attached_file_version_string.split("ver")[1])
except Exception as err:
    attached_version = 0
# only install from package if newer
if (float(attached_version) > float(installed_app_version
                                    )) and ProcessingApp.objects.filter(
        name=appname).first().is_enabled:
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


# defined app page
@ login_required
def view(request):

    args = {

        'SampleRecord':
        SampleRecord.objects.order_by('-pk'),
        'ProcessMethod': [f for f in os.listdir(
            "media/pd/methods/process/") if f.endswith('.pdProcessingWF')],
        'ConsensusMethod': [f for f in os.listdir(
            "media/pd/methods/consensus/") if f.endswith('.pdConsensusWF')],
    }
    processor = ProcessingApp.objects.filter(
        name=appname).first().process_package.name
    if processor:
        args['download_processor'] = os.path.join(
            settings.MEDIA_ROOT, processor)

    if request.method == 'POST':
        if (len(request.FILES) != 0 and
                request.POST.get('pd_process_option') == "custom"):
            pd_process_method = request.FILES['pd_process']
            if request.POST.get('keep_method') == "True":
                fs = FileSystemStorage(location="media/pd/methods/process/")
                fs.save(pd_process_method.name, pd_process_method)
        else:
            process_name = request.POST.get('pd_process_option')
            process_url = f'media/pd/methods/process/{process_name}'
            pd_process_method = InMemoryUploadedFile(open(
                process_url, 'r'), None, process_name, None, None, None)

        if (len(request.FILES) != 0 and
                request.POST.get('pd_consensus_option') == "custom"):
            pd_consensus_method = request.FILES['pd_consensus']
            if request.POST.get('keep_method') == "True":
                fs = FileSystemStorage(location="media/pd/methods/consensus/")
                fs.save(pd_consensus_method.name, pd_consensus_method)
        else:
            consensus_name = request.POST.get('pd_consensus_option')
            consensus_url = f'media/pd/methods/consensus/{consensus_name}'
            pd_consensus_method = InMemoryUploadedFile(open(
                consensus_url, 'r'), None, consensus_name, None, None, None)

        newqueue = {
            "processing_name": request.POST.get('analysis_name'),
            'processing_app': ProcessingApp.objects.filter(
                name=appname).first(),
            'process_creator': request.user,
            "input_file_1": pd_process_method,
            "input_file_2": pd_consensus_method,
            "keep_full_output": request.POST.get('keep_result'),
            "update_qc": request.POST.get('replace_qc'),




        }
        newtask = DataAnalysisQueue.objects.create(**newqueue, )
        for item in request.POST.getlist('rawfile_id'):
            newtask.sample_records.add(
                SampleRecord.objects.filter(pk=item).first())

    return render(request, 'filemanager/pd.html', args)


urlpatterns = [path("processing/pd/", view, name='Proteomic Discoverer')]
