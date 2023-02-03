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
appname = "Protein Discoverer Processor"


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

    return render(request, 'filemanager/protein_discoverer_processor.html', args)


urlpatterns = [path("processing/protein_discoverer_processor/",
                    view, name='Proteomic Discoverer Processor')]
