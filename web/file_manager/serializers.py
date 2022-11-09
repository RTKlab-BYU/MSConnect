from django.contrib.auth.models import User
from .models import FileStorage, SampleRecord, UserSettings, SystemSettings, \
    WorkerStatus, DataAnalysisQueue, ProcessingApp, VisualizationApp
from rest_framework import serializers


class FileStorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorage
        fields = ['pk', 'file_location', 'file_type']


class ProcessingAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingApp
        fields = ['pk', 'name']


class SampleRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleRecord
        fields = ['pk', 'record_name', 'record_description', "file_vendor",
                  'instrument_model', 'instrument_sn', "column_sn", "spe_sn",
                  "is_temp", "record_creator", "uploaded_time", "temp_rawfile",
                  "project_name", "sample_type", "factor_1_name", "newest_raw",
                  "factor_1_value", "factor_2_name", "factor_2_value",
                  "factor_3_name", "factor_3_value", "factor_4_name",
                  "factor_4_value", "factor_5_name", "factor_5_value",
                  "factor_6_name", "factor_6_value", "factor_7_name",
                  "factor_7_value", "factor_8_name", "factor_8_value"]


class WorkerStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerStatus
        fields = ['pk', 'processing_app', 'seq_number', 'worker_ip',
                  'worker_name', 'last_update', 'current_job']


class DataAnalysisQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataAnalysisQueue
        fields = ['pk', 'processing_app', 'sample_records', 'processing_name',
                  'worker_hostname', 'keep_full_output', 'update_qc',
                  'run_status', 'start_time', 'finish_time', 'process_creator',
                  'input_file_1', 'input_file_2', 'input_file_3',
                  'output_file_1', 'output_file_2', 'output_file_3',
                  'output_QC_number_1', 'output_QC_number_2',
                  'output_QC_number_3', 'output_QC_number_4'
                  ]
