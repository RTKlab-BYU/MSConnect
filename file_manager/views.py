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
import plotly.graph_objs as go
from plotly.graph_objs import Scatter
from plotly.offline import plot
import pickle
import shutil
import time
import os
import xmltodict
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import get_user_model
from django.core.files import File
from .models import RawFile, SpectromineQueue, SpectromineWorker, NoteFile, \
    SsdStorage, MaxquantQueue, MaxquantWorker, MsfraggerQueue, \
    MsfraggerWorker, PdQueue, PdWorker
from .serializers import RawFileSerializer, SpectromineQueueSerializer, \
    SpectromineWorkerSerializer, MaxquantQueueSerializer, \
    MaxquantWorkerSerializer, MsfraggerQueueSerializer, \
    MsfraggerWorkerSerializer, PdQueueSerializer, PdWorkerSerializer

User = get_user_model()
startTime = time.time()


@csrf_exempt
@api_view(['GET', 'POST', 'PUT'])
def auth(request):  # used for authenticated through API
    return Response({"message": "Hello, world!"})


@login_required
def dashboard(request):

    data_daily = RawFile.objects.all().annotate(date=TruncDay(
        'acquisition_time')).values("date").annotate(
        created_count=Count('id')).order_by("-date")
    data_monthly = RawFile.objects.all().annotate(month=TruncMonth(
        'acquisition_time')).values("month").annotate(
        created_count=Count('id')).order_by("-month")
    by_user = RawFile.objects.all().values("creator").annotate(
        total=Count('creator')).order_by('-total')
    daily_data = []
    daily_lables = []
    monthly_data = []
    monthly_lables = []
    user_names = []
    user_counts = []
    for n in range(0, 30):
        if data_daily[29-n]["date"] is not None:
            daily_lables.append(
                data_daily[29-n]["date"].strftime("%B-%d-%Y"))
            daily_data.append(data_daily[29-n]["created_count"])
    for n in range(0, 12):
        if data_monthly[11-n]["month"] is not None:
            monthly_lables.append(
                data_monthly[11-n]["month"].strftime("%B-%Y"))
            monthly_data.append(data_monthly[11-n]["created_count"])
    for item in by_user[:10]:
        if item["creator"] is not None:
            user_names.append(User.objects.get(
                id=int(item["creator"])).username)
            user_counts.append(item["total"])

    total, used, free = shutil.disk_usage("/")

    try:
        back_total, back_used, back_free =\
            shutil.disk_usage(
                "/home/rtklab/Documents/data_manager/media/hdstorage/")
    except OSError:
        # prevent error while debug on other systems
        back_total, back_used, back_free = 1*(2**30), 1*(2**30), 1*(2**30)

    try:
        remote_total, remote_used, remote_free =\
            shutil.disk_usage(
                "/home/rtklab/Documents/data_manager/media/remote_archive")
    except OSError:
        # prevent error while debug on other systems
        remote_total, remote_used, remote_free = 1 * \
            (2**30), 1*(2**30), 1*(2**30)

    try:
        offline_total, offline_used, offline_free =\
            shutil.disk_usage(
                "/home/rtklab/Documents/data_manager/media/hdstorage/")
    except OSError:
        # prevent error while debug on other systems
        offline_total, offline_used, offline_free = 1 * \
            (2**30), 1*(2**30), 1*(2**30)

    args = {
        "records": RawFile.objects.count(),
        "users": User.objects.count(),
        "time": int((time.time() - startTime)/3600),
        "total": int(total // (2**30)),
        "used": int(used // (2**30)),
        "free": int(free // (2**30)),
        "percent": int(free/total*100),
        'labels': ["used", "free"],
        'data': [int(used // (2**30)), int(free // (2**30))],
        "back_total": int(back_total // (2**30)),
        "back_used": int(back_used // (2**30)),
        "back_free": int(back_free // (2**30)),
        "back_percent": int(back_free/back_total*100),
        'back_labels': ["used", "free"],
        'back_data': [int(back_used // (2**30)), int(back_free // (2**30))],
        'remote_labels': ["used", "free"],
        'remote_data': [int(remote_used // (2**30)),
                        int(remote_free // (2**30))],
        'offline_labels': ["used", "free"],
        'offline_data': [int(offline_used // (2**30)),
                         int(offline_free // (2**30))],
        'daily_data': daily_data,
        'daily_labels': daily_lables,
        'monthly_data': monthly_data,
        'monthly_labels': monthly_lables,
        'user_data': user_counts,
        'user_labels': user_names,

    }

    return render(request, 'filemanager/dashboard.html', args)


def help(request):

    return render(request, 'filemanager/help.html')


@csrf_exempt
def uploadraw(request):
    if request.method == 'POST':
        form_data = {
            'run_name': request.POST.get('run_name'),
            'project_name': request.POST.get('project_name'),
            'run_desc': request.POST.get('run_desc'),
            'qc_tool': int(request.POST.get('qc_tool')),
            'temp_data': request.POST.get('tempdata'),
            'rawfile': request.FILES.get('raw_file'),

            # 'latest_calibration': "",
        }
        RawFile.objects.create(**form_data, )

    return render(request, 'filemanager/UploadRaw.html')


def results(request):

    args = {
        'RawFiles':
        RawFile.objects.all().order_by('-pk')[:100],
        'Current_message': "Last 100 uploaded runs",
        "users": User.objects.all(),

    }
    if request.method == 'POST' and 'data_filter' in request.POST:
        result_queryset = RawFile.objects.all().order_by('-pk')
        if request.POST.get('run_name') != "":
            result_queryset = result_queryset.filter(
                run_name__contains=request.POST.
                get('run_name')).order_by('-pk')
        if request.POST.get('project_name') != "":
            result_queryset = result_queryset.filter(
                project_name__contains=request.POST.get(
                    'project_name')).order_by('-pk')
        if request.POST.get('run_desc') != "":
            result_queryset = result_queryset.filter(
                run_desc__contains=request.POST.
                get('run_desc')).order_by('-pk')
        if request.POST.get('instrument_sn') != "":
            result_queryset = result_queryset.filter(
                instrument_sn__contains=request.POST.
                get('instrument_sn')).order_by('-pk')
        if request.POST.get('notes') != "":
            result_queryset = result_queryset.filter(
                notes__contains=request.POST.get('notes')).order_by('-pk')
        if request.POST.get('user') != "":
            result_queryset = result_queryset.filter(
                creator=request.POST.get('user')).order_by('-pk')
        if request.POST.get('start_time') != "" and request.POST.get(
                'end_time') != "":
            result_queryset = result_queryset.filter(acquisition_time__range=[
                request.POST.get(
                    'start_time'), request.POST.get('end_time')+" 23:59"]
            ).order_by('-pk')
        if request.POST.get('custom_value') != "" and request.POST.get(
                'custom_para') != "":
            variable_column = request.POST.get('custom_para')
            search_type = 'contains'
            filter = variable_column + '__' + search_type
            result_queryset = result_queryset.filter(
                **{filter: request.POST.get('custom_value')}).order_by('-pk')

        args = {
            'RawFiles': result_queryset,
            'Current_message':
                f"Search resulted {len(result_queryset)} records",
            "formdata": request.POST,
            "users": User.objects.all()


        }

    return render(request, 'filemanager/results.html', args)


def process(request):
    args = {
        'SpectromineQueue':
        SpectromineQueue.objects.all().order_by('-pk')[:100],
        'RawFiles':
        RawFile.objects.all(),
        'SpectromineWorker': SpectromineWorker.objects.first(),

    }
    if request.method == 'POST':

        newqueue = {
            'rawfile': RawFile.objects.filter(
                pk=request.POST.get('rawFile_selector')).first(),
            'creator': request.user,
        }
        SpectromineQueue.objects.create(**newqueue, )

    return render(request, 'filemanager/process.html', args)


def msfragger(request):
    args = {
        'MsfraggerQueue':
        MsfraggerQueue.objects.all().order_by('-pk')[:100],
        'RawFiles':
        RawFile.objects.order_by('-pk'),
        'MsfraggerWorker': MsfraggerWorker.objects.first(),

    }
    if request.method == 'POST':

        newqueue = {
            'creator': request.user,
        }
        new_queue_obj = MsfraggerQueue.objects.create(**newqueue, )
        new_queue_obj.rawfile.add(RawFile.objects.filter(
            pk=request.POST.get('rawFile_selector')).first(),)
        new_queue_obj.save()
    return render(request, 'filemanager/msfragger.html', args)


def pd(request):
    args = {
        'PdQueue':
        PdQueue.objects.all().order_by('-pk')[:100],
        'RawFiles':
        RawFile.objects.order_by('-pk'),
        'PdWorker': PdWorker.objects.first(),

    }

    if request.method == 'POST':
        print(request.POST)
        if (len(request.FILES) != 0 and
                request.POST.get('pd_process_option') == "custom"):
            pd_process_method = request.FILES['pd_process']
        else:
            local_file = open(os.path.join(
                "media/pd/", request.POST.get('pd_process_option') +
                ".pdProcessingWF"))
            pd_process_method = File(local_file)

        if (len(request.FILES) != 0 and
                request.POST.get('pd_consensus_option') == "custom"):
            pd_consensus_method = request.FILES['pd_consensus']
        else:
            local_file = open(os.path.join(
                "media/pd/", request.POST.get('pd_consensus_option') +
                ".pdConsensusWF"))
            pd_consensus_method = File(local_file)

        newqueue = {
            "analysis_name": request.POST.get('analysis_name'),
            'creator': request.user,
            "processing_method": pd_process_method,
            "consensus_method": pd_consensus_method,
            "keep_result": request.POST.get('keep_result'),
            "TMT": request.POST.get('TMT'),




        }
        newtask = PdQueue.objects.create(**newqueue, )
        for item in request.POST.getlist('rawfile_id'):
            newtask.rawfile.add(RawFile.objects.filter(pk=item).first())

    return render(request, 'filemanager/protein_discoverer.html', args)


def maxquant(request):
    args = {
        'MaxquantQueue':
        MaxquantQueue.objects.all().order_by('-pk')[:100],
        'RawFiles':
        RawFile.objects.all().order_by('-pk'),
        'MaxquantWorker': MaxquantWorker.objects.first(),

    }

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
            "analysis_name": request.POST.get('analysis_name'),
            'creator': request.user,
            "setting_xml": InMemoryUploadedFile(open(
                'media/maxquant/mqpar.xml', 'r'), None, 'mqpar.xml', None,
                None, None),
        }
        newtask = MaxquantQueue.objects.create(**newqueue, )
        for item in request.POST.getlist('rawfile_id'):
            newtask.rawfile.add(RawFile.objects.filter(pk=item).first())

    return render(request, 'filemanager/maxquant.html', args)


def load_results(request, pk, *args, **kwargs):
    if pk == 9990999:  # used for debuging
        from schedule_archive.automated_tasks import remove_unused_files
        remove_unused_files(SsdStorage, 4)

    message = ""
    if request.method == 'POST' and 'delete' in request.POST:
        if request.user == RawFile.objects.filter(pk=pk)[0].creator or\
                RawFile.objects.filter(pk=pk)[0].creator is None:
            RawFile.objects.filter(pk=pk).delete()
            return HttpResponseRedirect("/files/results/")
        else:
            message = "Sorry, you don't own this record"
    if request.method == 'POST' and 'save' in request.POST:
        print(request.POST)
        if request.user == RawFile.objects.filter(pk=pk)[0].creator or\
                RawFile.objects.filter(pk=pk)[0].creator is None:
            RawFile.objects.filter(pk=pk).update(
                notes=request.POST.get('notes'))
            RawFile.objects.filter(pk=pk).update(
                run_desc=request.POST.get('desc'))
            RawFile.objects.filter(pk=pk).update(
                temp_data=request.POST.get('tempdata'))
            RawFile.objects.filter(pk=pk).update(
                run_name=request.POST.get('name'))
            RawFile.objects.filter(pk=pk).update(
                project_name=request.POST.get('projectname'))
            RawFile.objects.filter(pk=pk).update(
                plot_label=request.POST.get('plot_label'))
            if request.FILES.get('notefile') is not None:
                notefileform = {"notefile": request.FILES.get('notefile')}
                RawFile.objects.filter(pk=pk)[0].note_file.add(
                    NoteFile.objects.create(**notefileform, ))
        else:
            message = "Sorry, you don't own this record"
    notes = RawFile.objects.filter(pk=pk)[0].note_file.all()
    notelist = []
    for item in notes:
        notelist.append(item.notefile)

    if request.method == 'POST' and 'compare' in request.POST:
        compareid = int(request.POST.get('compare_id'))
        if (RawFile.objects.filter(pk=pk)[0].pklfile.name is not None and
                RawFile.objects.filter(pk=compareid)[0].pklfile.name
                is not None):
            filename = os.path.join(
                settings.MEDIA_ROOT,
                RawFile.objects.filter(pk=pk)[0].pklfile.name)
            filename2 = os.path.join(
                settings.MEDIA_ROOT,
                RawFile.objects.filter(pk=compareid)[0].pklfile.name)
            with open(filename, 'rb') as handle:
                plot_data = pickle.load(handle)
            with open(filename2, 'rb') as handle2:
                plot_data2 = pickle.load(handle2)
            plot_div = plot({"data":
                             [Scatter(x=plot_data["MS1_RT"],
                                      y=plot_data["MS1_Basemzintensity"],
                                      mode='lines',
                                      name='BIC',
                                      opacity=0.8,
                                      marker_color='green',
                                      yaxis='y1',
                                      line=dict(width=1,)),
                              Scatter(x=plot_data["MS1_RT"],
                                      y=plot_data["MS1_Ticintensity"],
                                      mode='lines',
                                      name='TIC',
                                      opacity=0.8,
                                      marker_color='Red',
                                      yaxis='y1',
                                      visible='legendonly',
                                      line=dict(width=1,)),
                              Scatter(x=plot_data["MS1_RT"],
                                      y=plot_data["MS1_Basemz"],
                                      mode='lines',
                                      name='m/z',
                                      opacity=0.8,
                                      marker_color='yellow',
                                      visible='legendonly',
                                      yaxis='y1'),
                              Scatter(x=plot_data["MS2_RT"],
                                      y=plot_data["MS2_Injectiontime"],
                                      mode='lines',
                                      name='MS2 Injection Time',
                                      opacity=0.8,
                                      marker_color='blue',
                                      visible='legendonly',
                                      yaxis='y2'),
                              Scatter(x=plot_data2["MS1_RT"],
                                      y=plot_data2["MS1_Basemzintensity"],
                                      mode='lines',
                                      name=f'{compareid} BIC',
                                      opacity=0.8,
                                      marker_color='olive',
                                      yaxis='y1',
                                      line=dict(width=1,)),
                              Scatter(x=plot_data2["MS1_RT"],
                                      y=plot_data2["MS1_Ticintensity"],
                                      mode='lines',
                                      name=f'{compareid} TIC',
                                      opacity=0.8,
                                      marker_color='darkred',
                                      yaxis='y1',
                                      visible='legendonly',
                                      line=dict(width=1,)),
                              Scatter(x=plot_data2["MS1_RT"],
                                      y=plot_data2["MS1_Basemz"],
                                      mode='lines',
                                      name=f'{compareid} m/z',
                                      opacity=0.8,
                                      marker_color='dodgerblue',
                                      visible='legendonly',
                                      yaxis='y1'),
                              Scatter(x=plot_data2["MS2_RT"],
                                      y=plot_data2["MS2_Injectiontime"],
                                      mode='lines',
                                      name=f'{compareid} MS2 Injection Time',
                                      opacity=0.8,
                                      marker_color='firebrick',
                                      visible='legendonly',
                                      yaxis='y2')],
                             "layout":
                             go.Layout(yaxis=dict(title='Ion Intensity /Ab'),
                                       yaxis2=dict(title='Injection Time /ms',
                                                   overlaying='y',
                                                   side='right'))},
                            output_type='div', show_link=False, link_text="")
        else:
            plot_div = None

    else:
        if (RawFile.objects.filter(pk=pk)[0].pklfile.name is not None):
            filename = os.path.join(
                settings.MEDIA_ROOT,
                RawFile.objects.filter(pk=pk)[0].pklfile.name)
            try:
                with open(filename, 'rb') as handle:
                    plot_data = pickle.load(handle)
                    plot_div = plot({"data":
                                     [Scatter(x=plot_data["MS1_RT"],
                                              y=plot_data[
                                         "MS1_Basemzintensity"],
                                         mode='lines',
                                         name='BIC',
                                         opacity=0.8,
                                         marker_color='green',
                                         yaxis='y1',
                                         line=dict(width=1,)),
                                      Scatter(x=plot_data["MS1_RT"],
                                              y=plot_data["MS1_Ticintensity"],
                                              mode='lines',
                                              name='TIC',
                                              opacity=0.8,
                                              marker_color='Red',
                                              yaxis='y1',
                                              visible='legendonly',
                                              line=dict(width=1,)),
                                      Scatter(x=plot_data["MS1_RT"],
                                              y=plot_data["MS1_Basemz"],
                                              mode='lines',
                                              name='m/z',
                                              opacity=0.8,
                                              marker_color='blue',
                                              visible='legendonly',
                                              yaxis='y1'),
                                      Scatter(x=plot_data["MS2_RT"],
                                              y=plot_data["MS2_Injectiontime"],
                                              mode='lines',
                                              name='MS2 Injection Time',
                                              opacity=0.8,
                                              marker_color='blue',
                                              visible='legendonly',
                                              yaxis='y2')],
                                     "layout":
                                     go.Layout(
                                         yaxis=dict(title='Ion Intensity /Ab'),
                                         yaxis2=dict(
                                             title='Injection Time /ms',
                                             overlaying='y',
                                             side='right'))},
                                    output_type='div',
                                    show_link=False,
                                    link_text="")
            except OSError:
                plot_div = None

        else:
            plot_div = None

    args = {
        "detail": RawFile.objects.filter(pk=pk)[0],
        "notefile": notelist,
        "message": message,
        "plot_div": plot_div
    }
    return render(request, 'filemanager/detail.html', args)


class FileList(generics.ListCreateAPIView):
    queryset = RawFile.objects.all()
    serializer_class = RawFileSerializer


class FileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = RawFile.objects.all()
    serializer_class = RawFileSerializer


class SpectromineQueueList(generics.ListCreateAPIView):
    queryset = SpectromineQueue.objects.filter(
        run_status=False).all().order_by('-pk')[:100]
    serializer_class = SpectromineQueueSerializer


class SpectromineQueueDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SpectromineQueue.objects.all()
    serializer_class = SpectromineQueueSerializer


class SpectromineWorkerList(generics.ListCreateAPIView):
    queryset = SpectromineWorker.objects.all()
    serializer_class = SpectromineWorkerSerializer


class SpectromineWorkerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SpectromineWorker.objects.all()
    serializer_class = SpectromineWorkerSerializer


class MaxquantQueueList(generics.ListCreateAPIView):
    queryset = MaxquantQueue.objects.filter(
        run_status=False).all().order_by('-pk')[:100]
    serializer_class = MaxquantQueueSerializer


class MaxquantQueueDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = MaxquantQueue.objects.all()
    serializer_class = MaxquantQueueSerializer


class MaxquantWorkerList(generics.ListCreateAPIView):
    queryset = MaxquantWorker.objects.all()
    serializer_class = MaxquantWorkerSerializer


class MaxquantWorkerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = MaxquantWorker.objects.all()
    serializer_class = MaxquantWorkerSerializer


class MsfraggerQueueList(generics.ListCreateAPIView):
    queryset = MsfraggerQueue.objects.filter(
        run_status=False).all().order_by('-pk')[:100]
    serializer_class = MsfraggerQueueSerializer


class MsfraggerQueueDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = MsfraggerQueue.objects.all()
    serializer_class = MsfraggerQueueSerializer


class MsfraggerWorkerList(generics.ListCreateAPIView):
    queryset = MsfraggerWorker.objects.all()
    serializer_class = MsfraggerWorkerSerializer


class MsfraggerWorkerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = MsfraggerWorker.objects.all()
    serializer_class = MsfraggerWorkerSerializer


class PdQueueList(generics.ListCreateAPIView):
    queryset = PdQueue.objects.filter(
        run_status=False).all().order_by('-pk')[:100]
    serializer_class = PdQueueSerializer


class PdQueueDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PdQueue.objects.all()
    serializer_class = PdQueueSerializer


class PdWorkerList(generics.ListCreateAPIView):
    queryset = PdWorker.objects.all()
    serializer_class = PdWorkerSerializer


class PdWorkerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PdWorker.objects.all()
    serializer_class = PdWorkerSerializer
