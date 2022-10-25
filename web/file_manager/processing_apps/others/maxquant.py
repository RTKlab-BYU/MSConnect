import xmltodict
import os
from zipfile import ZipFile
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
from file_manager .models import FileStorage, SampleRecord, UserSettings, \
    SystemSettings, WorkerStatus, DataAnalysisQueue, Review, \
    AppAuthor, ProcessingApp, VisualizationApp

# app name, must be the same as in the database
appname = "Maxquant"

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
if (attached_version > installed_app_version
    ) and ProcessingApp.objects.filter(
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


@ login_required
def view(request):
    args = {
        'SampleRecord':
        SampleRecord.objects.order_by('-pk'), }
    processor = ProcessingApp.objects.filter(
        name=appname).first().process_package.name
    if processor:
        args['download_processor'] = os.path.join(
            settings.MEDIA_ROOT, processor)

    if request.method == 'POST':
        if (len(request.FILES) != 0 and
                request.POST.get('maxquant_settings') == "custom"):
            myfile = request.FILES['maxquant_xml']
            fs = FileSystemStorage(location="media/maxquant/")
            custom_file = fs.save("custom", myfile)
            print(custom_file)
            with open(os.path.join("media/maxquant/",
                                   custom_file), "r") as xml_obj:
                # coverting the xml data to Python dictionary
                my_dict = xmltodict.parse(xml_obj.read())
            print(my_dict)
            os.remove(os.path.join("media/maxquant/", custom_file))
        else:
            with open(os.path.join("media/maxquant/", request.POST.get(
                    'maxquant_settings')), "r") as xml_obj:
                # coverting the xml data to Python dictionary
                my_dict = xmltodict.parse(xml_obj.read())
        xml_obj.close()
        filestr = []
        for item in request.POST.getlist('rawfile_id'):
            filestr.append("c:\\maxquant_temp\\"+item+".raw")
        my_dict['MaxQuantParams']["fastaFiles"]['FastaFileInfo'][
            'fastaFilePath'] = "c:\\maxquant_settings\\fasta\\" + \
            request.POST.get('fasta_file')+".fasta"
        my_dict['MaxQuantParams']["filePaths"]['string'] = filestr
        my_dict['MaxQuantParams']["experiments"][
            'string'] = request.POST.getlist('rawfile_id')
        my_dict['MaxQuantParams']["fractions"]['short'] = request.POST.getlist(
            'fraction')
        my_dict['MaxQuantParams']["ptms"]['boolean'] = request.POST.getlist(
            'ptm')
        my_dict['MaxQuantParams']["paramGroupIndices"][
            'int'] = request.POST.getlist('paragroup')
        my_dict['MaxQuantParams']["referenceChannel"][
            'string'] = request.POST.getlist('reference')

        setting_xml = open('media/maxquant/mqpar.xml', 'w')
        setting_xml.write(xmltodict.unparse(my_dict, pretty=True))
        setting_xml.close()

        newqueue = {
            "processing_name": request.POST.get('analysis_name'),
            'processing_app': ProcessingApp.objects.filter(
                name=appname).first(),
            'process_creator': request.user,
            "input_file_1": InMemoryUploadedFile(open(
                'media/maxquant/mqpar.xml', 'r'), None, 'mqpar.xml', None,
                None, None),
            "update_qc": request.POST.get('replace_qc'),


        }

        newtask = DataAnalysisQueue.objects.create(**newqueue, )
        for item in request.POST.getlist('rawfile_id'):
            newtask.sample_records.add(
                SampleRecord.objects.filter(pk=item).first())

    return render(request, 'filemanager/maxquant.html', args)


urlpatterns = [path("processing/maxquant/", view, name='Maxquant')]
