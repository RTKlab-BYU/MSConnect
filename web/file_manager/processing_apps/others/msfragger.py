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
import pickle
import shutil
import time
import os
import xmltodict
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import get_user_model
from django.core.files import File
from django.urls import path, include

from django.conf.urls.static import static
from django.conf import settings
from rest_framework import routers


@ login_required
def view(request):
    args = {}

    return render(request, 'filemanager/msfragger.html', args)


urlpatterns = [path("processing/msfragger/", view, name='Msfragger')]
