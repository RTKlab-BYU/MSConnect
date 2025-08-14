"""
Define the app pages for the project.
"""

# Standard library imports
import logging
import os
import random
import string
import subprocess
import shutil
import time
import glob


# Third-party imports
import requests
import plotly.graph_objs as go
import pickle
import numpy as np
from datetime import datetime, timedelta
from plotly.graph_objs import Scatter
from plotly.offline import plot
from zipfile import ZipFile
from urllib.request import urlretrieve, urlcleanup
from urllib.parse import urlsplit

# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.admin.views.decorators import staff_member_required
from django.core import management
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage

from django.http import HttpResponseRedirect, FileResponse, Http404, HttpResponse
from django.shortcuts import render
from django.utils.timezone import utc
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import IsAdminUser


# Django REST Framework imports
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.
@ login_required
def graphs_view(request):
    return render(request, 'filemanager/graphs.html')

@ csrf_exempt
def run_graph_pipeline(request):
    if request.method == 'POST':
        # Save uploaded files
        fs = FileSystemStorage(location='input')
        protein_file = request.FILES.get('protein_file')
        peptide_file = request.FILES.get('peptide_file')

        protein_path = fs.save(protein_file.name, protein_file) if protein_file else None
        peptide_path = fs.save(peptide_file.name, peptide_file) if peptide_file else None

        # Extract form data
        graph_type = request.POST.get('graph_type')
        transform_flags = [
            'transform_filter_missing',
            'transform_filter_contaminants',
            'transform_log2',
            'transform_normalize',
            'transform_impute',
            'transform_batch_correction',
            'transform_iqr_outliers',
            'transform_zscore_outliers',
        ]
        transforms = ['True' if request.POST.get(f) else 'False' for f in transform_flags]

        # Build command list
        def build_command(target):
            return [
                'python3', 'path/to/transformation_script.py',
                'diann',
                target,
                *transforms
            ]

        cmds_to_run = []

        if graph_type in ['bar', 'box', 'violin']:
            if protein_path:
                cmds_to_run.append(build_command('protein'))
            if peptide_path:
                cmds_to_run.append(build_command('peptide'))
        else:
            if protein_path:
                cmds_to_run.append(build_command('protein'))
            elif peptide_path:
                cmds_to_run.append(build_command('peptide'))

        # Run each command
        for cmd in cmds_to_run:
            subprocess.run(cmd)

        # Handle volcano condition info if needed (not yet processed in script)

        return redirect('/files/graphs/')

    return redirect('/files/graphs/')

@ login_required
def run_graph_pipeline(request):
    if request.method == 'POST':
        # Save uploaded files
        protein_file = request.FILES.get('protein_file')
        peptide_file = request.FILES.get('peptide_file')

        os.makedirs('input', exist_ok=True)
        input_protein_path = None
        input_peptide_path = None

        if protein_file:
            input_protein_path = default_storage.save('input/protein.tsv', protein_file)
        if peptide_file:
            input_peptide_path = default_storage.save('input/peptide.tsv', peptide_file)

        # Graph selection
        graph_type = request.POST.get('graph_type')

        # Determine data target
        target = 'protein' if protein_file else 'peptide'
        input_file_path = os.path.join(settings.MEDIA_ROOT, input_protein_path or input_peptide_path)

        # Build transformation command
        transform_args = [
            'python', 'data_transformation.py',
            'diann',  # filetype (assume DIA-NN for now)
            target,
            request.POST.get('transform_filter_missing', 'False'),
            request.POST.get('transform_filter_contaminants', 'False'),
            request.POST.get('transform_log2', 'False'),
            request.POST.get('transform_normalize', 'False'),
            request.POST.get('transform_impute', 'False'),
            request.POST.get('transform_batch_correction', 'False'),
            request.POST.get('transform_iqr_outliers', 'False'),
            request.POST.get('transform_zscore_outliers', 'False'),
        ]

        # Run transformation
        subprocess.run(transform_args, check=True)

        # Call appropriate graph script
        if graph_type == 'box':
            subprocess.run(['python', 'graphs/box_plot.py', target], check=True)
        elif graph_type == 'violin':
            subtype = request.POST.get('violin_subtype')  # id_plot or cv_plot
            subprocess.run(['python', f'graphs/violin_plot_{subtype}.py', target], check=True)
        elif graph_type == 'bar':
            subprocess.run(['python', 'graphs/bar_plot.py', target], check=True)
        elif graph_type == 'venn':
            subprocess.run(['python', 'graphs/venn.py'], check=True)
        elif graph_type == 'volcano':
            # Handle volcano condition info
            condition_info = request.POST.get('volcano_condition_info', '')
            subprocess.run(['python', 'graphs/volcano_plot.py', target, condition_info], check=True)
        elif graph_type == 'heatmap':
            # Handle heatmap condition info
            condition_info = request.POST.get('heatmap_condition_info', '')
            subprocess.run(['python', 'graphs/heatmap.py', target, condition_info], check=True)
        elif graph_type == 'PCA':
            # Handle PCA condition info
            condition_info = request.POST.get('pca_condition_info', '')
            subprocess.run(['python', 'graphs/pca_plot.py', target, condition_info], check=True)
        elif graph_type == 't-SNE':
            # Handle t-SNE condition info
            condition_info = request.POST.get('tsne_condition_info', '')
            subprocess.run(['python', 'graphs/tsne_plot.py', target, condition_info], check=True)

        return HttpResponse("Graph generated successfully.")
    return HttpResponse("Invalid request.")
