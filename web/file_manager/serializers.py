from django.contrib.auth.models import User
from .models import FileStorage, SampleRecord, UserSettings, SystemSettings, \
    WorkerStatus, DataAnalysisQueue, Review, \
    AppAuthor, ProcessingApp, VisualizationApp
from rest_framework import serializers


class FileStorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorage
        fields = ['pk', 'file_location', 'file_type', 'modified_time']


class SampleRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleRecord
        fields = ['pk', 'record_name', 'record_description',
                  'instrument_model', 'instrument_SN', "column_sn", "spe_sn",
                  "quanlity_check", "is_temp", "record_creator",
                  "acquisition_time", "uploaded_time", "temp_rawfile",
                  "sample_info", "file_size", "is_processed",
                  "file_storage_indeces", "cache_pkl", "file_attachments",
                  "newest_raw"]


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
