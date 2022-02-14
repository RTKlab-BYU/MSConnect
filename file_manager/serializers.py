from .models import RawFile, SpectromineQueue, SpectromineWorker, \
    MaxquantQueue, MaxquantWorker, MsfraggerQueue, MsfraggerWorker, \
    PdQueue, PdWorker
from rest_framework import serializers


class RawFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawFile
        fields = ['pk', 'run_name', 'project_name', 'run_desc',
                  'qc_tool', "qc_mbr", "instrument_model", "instrument_sn",
                  "creator", "notes", "note_file", "temp_data", "rawfile",
                  "uploaded_at", "acquisition_time", "sample_type",
                  "pklfile", "content_type", "object_id", "ssd_storage",
                  "hd_storage", "remote_storage",  "offline_storage",
                  "column_sn", "spe_sn", "sample_obj", "storage_option"]


class SpectromineQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpectromineQueue
        fields = ['pk', 'run_status', 'protein_id', 'peptide_id',
                  'start_time', 'finished_time', 'creator',
                  "result_file", "rawfile"]


class SpectromineWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpectromineWorker
        fields = ['pk', 'worker_name', 'worker_ip', 'worker_status',
                  'current_job', 'current_percentage', 'last_update']


class MaxquantQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaxquantQueue
        fields = ['pk', 'run_status', 'protein_id', 'peptide_id',
                  'start_time', 'finished_time', 'creator',
                  "rawfile", "setting_xml", "evidence_file",
                  "protein_file", "peptide_file", "other_file"]
        extra_kwargs = {
            'rawfile': {'read_only': True},
        }


class MaxquantWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaxquantWorker
        fields = ['pk', 'worker_name', 'worker_ip', 'worker_status',
                  'current_job', 'current_percentage', 'last_update']


class MsfraggerQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsfraggerQueue
        fields = ['pk', 'run_status', 'precurosr_id', 'psm_id', 'protein_id',
                  'peptide_id', 'start_time', 'finished_time', 'creator',
                  'rawfile', 'ion_file', 'psm_file', 'protein_file',
                  'peptide_file']
        extra_kwargs = {
            'rawfile': {'read_only': True},
        }


class MsfraggerWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsfraggerWorker
        fields = ['pk', 'worker_name', 'worker_ip', 'worker_status',
                  'current_job', 'current_percentage', 'last_update']


class PdQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdQueue
        fields = ['pk', 'run_status', 'precurosr_id', 'psm_id', 'protein_id',
                  'peptide_id', 'start_time', 'finished_time', 'creator',
                  'processing_method', 'consensus_method', 'export_file',
                  'keep_result', 'TMT', 'rawfile', 'result_file']
        extra_kwargs = {
            'rawfile': {'read_only': True},
        }


class PdWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdWorker
        fields = ['pk', 'worker_name', 'worker_ip', 'worker_status',
                  'current_job', 'last_update']
