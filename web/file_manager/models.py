from django.db import models
from django.conf import settings
from datetime import date
import datetime
import xmltodict

from django_currentuser.db.models import CurrentUserField
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
import pickle
import os
import io
import zipfile
from django.core.files import File
import subprocess
import time
import shutil
from django.utils import timezone
import json
from os.path import exists
import random
import string
from django.db.models.signals import post_save


from django.dispatch import receiver
from django.contrib.contenttypes import fields
from .File_converter import FileConverter


class FileStorage(models.Model):
    '''
 file_type: 0: cache/pkl
            1-4 raw four different locations
            5 note files
            6-9 process file different locations


'''
    file_location = models.FileField(blank=True, null=True)
    file_type = models.TextField(max_length=10, blank=True, null=True)


class SampleRecord(models.Model):
    """This is the main class, used to describe a MS record
    """
    record_name = models.TextField(max_length=100, blank=True, null=True)
    record_description = models.TextField(
        max_length=1000, blank=True, null=True)
    instrument_model = models.TextField(max_length=100, blank=True, null=True)
    instrument_sn = models.TextField(max_length=100, blank=True, null=True)

    column_sn = models.TextField(max_length=100, blank=True, null=True)
    spe_sn = models.TextField(max_length=100, blank=True, null=True)
    quanlity_check = models.ForeignKey(
        "DataAnalysisQueue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_temp = models.BooleanField(default=False, null=True)
    notes = models.TextField(max_length=1000, blank=True, null=True)

    record_creator = CurrentUserField()
    acquisition_time = models.DateTimeField(blank=True, null=True)
    uploaded_time = models.DateTimeField(auto_now_add=True)
    temp_rawfile = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/temp/", blank=True, null=True)
    file_size = models.DecimalField(default=0, max_digits=5,
                                    decimal_places=3, blank=True, null=True)
    is_processed = models.BooleanField(default=False, null=True)
    file_storage_indeces = models.ManyToManyField(
        FileStorage, related_name="storage", blank=True)
    cache_pkl = models.ForeignKey(
        "FileStorage",
        related_name="cache_pkl",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    file_attachments = models.ManyToManyField(
        FileStorage, related_name="attachments", blank=True)

    newest_raw = models.ForeignKey(
        "FileStorage",
        related_name="newest_raw",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project_name = models.TextField(max_length=100, blank=True, null=True)
    sample_type = models.TextField(max_length=100, blank=True, null=True)
    factor_1_name = models.TextField(max_length=100, blank=True, null=True)
    factor_1_value = models.TextField(
        max_length=100, blank=True, null=True)
    factor_2_name = models.TextField(max_length=100, blank=True, null=True)
    factor_2_value = models.TextField(
        max_length=100, blank=True, null=True)
    factor_3_name = models.TextField(max_length=100, blank=True, null=True)
    factor_3_value = models.TextField(
        max_length=100, blank=True, null=True)
    factor_4_name = models.TextField(max_length=100, blank=True, null=True)
    factor_4_value = models.TextField(
        max_length=100, blank=True, null=True)
    factor_5_name = models.TextField(max_length=100, blank=True, null=True)
    factor_5_value = models.TextField(
        max_length=100, blank=True, null=True)
    factor_6_name = models.TextField(max_length=100, blank=True, null=True)
    factor_6_value = models.TextField(
        max_length=100, blank=True, null=True)
    factor_7_name = models.TextField(max_length=100, blank=True, null=True)
    factor_7_value = models.TextField(
        max_length=100, blank=True, null=True)
    factor_8_name = models.TextField(max_length=100, blank=True, null=True)
    factor_8_value = models.TextField(
        max_length=100, blank=True, null=True)


@receiver(post_save, sender=SampleRecord, dispatch_uid="process uploaded file")
def process_uploaded(sender, instance, **kwargs):
    """procee the raw file once recrod created and file uploaded
    including file convertion, meta info extraction, flag: is_processed
    """

    if not instance.is_processed:
        convert = FileConverter(instance, FileStorage)

        if convert.sucess:
            # Automatically create QC based on user settings(app/preset)
            if UserSettings.objects.filter(
                    user=instance.record_creator.pk).first() is None:
                auto_qc = "None"

            else:
                auto_qc = UserSettings.objects.filter(
                    pk=instance.record_creator.pk).first(
                ).QC_pro_tool
            if auto_qc != "None":

                qc_setting_list = auto_qc.split("qc")
                # list item 1 is qc app pk, 2 is qc preset number
                process_app = ProcessingApp.objects.filter(
                    pk=qc_setting_list[0]).first()

                newqueue = {
                    "processing_name": instance.pk,
                    'processing_app': process_app,
                    'process_creator': instance.record_creator,

                }

                newtask = DataAnalysisQueue.objects.create(**newqueue, )
                newtask.sample_records.add(
                    SampleRecord.objects.filter(pk=instance.pk).first())

                # attach preset input files into queue
                preset_file = os.path.join(
                    settings.MEDIA_ROOT, getattr(
                        process_app, f"preset_{qc_setting_list[1]}").name)
                with zipfile.ZipFile(preset_file, 'r') as z:
                    for target_file in z.namelist():
                        for n in range(1, 4):
                            if target_file.startswith(f'input_file_{n}'):
                                with z.open(target_file) as myfile:
                                    with io.BytesIO() as buf:
                                        buf.write(myfile.read())
                                        buf.seek(0)
                                        # File, an import of django.core.files
                                        setattr(
                                            newtask, f"input_file_{n}", File(
                                                buf, target_file))
                                        newtask.save()

                SampleRecord.objects.filter(pk=instance.pk).update(
                    quanlity_check=newtask.pk)

    SampleRecord.objects.filter(pk=instance.pk).update(
        is_processed=True)


class UserSettings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True,
                             null=True)

    hide_othersresult = models.BooleanField(default=False, null=True)
    hide_other_apps = models.BooleanField(default=False, null=True)
    # formate for qc_pro_tool is process_app_pk + "qc" + preset_number
    QC_pro_tool = models.TextField(
        max_length=100, blank=True, null=True, default="None")
    qc_1_name = models.TextField(
        max_length=100, blank=True, null=True, default="Protein")
    qc_2_name = models.TextField(
        max_length=100, blank=True, null=True, default="Peptide")
    qc_3_name = models.TextField(
        max_length=100, blank=True, null=True, default="PSM")
    qc_4_name = models.TextField(
        max_length=100, blank=True, null=True, default="MS2")

    def __str__(self):
        return 'Profile of user: {}'.format(self.user.username)


class SystemSettings(models.Model):
    """_Four storages:primary_storage,secondary_storage, remote_storage,
     offline_storage, will be mounted through docker or ubuntu itself_
    Args:
        models (_type_): _description_
    """

    facility_name = models.TextField(
        max_length=1000, blank=True, default="My", null=True)
    auto_backup_settings = models.JSONField(default=dict, null=True)
    auto_purge_settings = models.JSONField(default=dict, null=True)
    systemfile_backup_settings = models.JSONField(default=dict, null=True)

    system_version = models.TextField(
        max_length=1000, blank=True, null=True)


class WorkerStatus(models.Model):
    processing_app = models.ForeignKey(
        "ProcessingApp",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    seq_number = models.IntegerField(blank=True, null=True, default=0)
    worker_ip = models.TextField(max_length=100, blank=True, null=True)
    worker_name = models.TextField(max_length=100, blank=True, null=True)
    last_update = models.TextField(max_length=100, blank=True, null=True)
    current_job = models.TextField(max_length=100, blank=True, null=True)


class DataAnalysisQueue(models.Model):
    """used to describe  data process queue."""
    processing_app = models.ForeignKey(
        "ProcessingApp",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sample_records = models.ManyToManyField(SampleRecord)
    processing_name = models.TextField(
        max_length=100, blank=True, null=True)
    worker_hostname = models.TextField(
        max_length=100, blank=True, null=True)
    keep_full_output = models.BooleanField(default=False, null=True)
    update_qc = models.BooleanField(default=False, null=True)
    run_status = models.BooleanField(default=False, null=True)
    submit_time = models.DateTimeField(auto_now_add=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    process_creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                        on_delete=models.SET_NULL, blank=True,
                                        null=True)
    input_file_1 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    input_file_2 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    input_file_3 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    output_file_1 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    output_file_2 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    output_file_3 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    backup_indeces = models.ManyToManyField(
        FileStorage, related_name="procee_queue_backup", blank=True)

    output_QC_number_1 = models.IntegerField(blank=True, null=True)
    output_QC_number_2 = models.IntegerField(blank=True, null=True)
    output_QC_number_3 = models.IntegerField(blank=True, null=True)
    output_QC_number_4 = models.IntegerField(blank=True, null=True)


@receiver(post_save, sender=DataAnalysisQueue, dispatch_uid="move files")
def move_file(sender, instance, **kwargs):
    """_move uploaded file to year/month/date folder_
    """
    file_list = ["input_file_1", "input_file_2", "input_file_3",
                 "output_file_1", "output_file_2", "output_file_3", ]
    update_url = {}
    for item in file_list:
        old_file_path = getattr(instance, item).name
        if old_file_path:
            if "uniquetempfolder" in old_file_path:
                to_tz = timezone.get_default_timezone()
                submit_time = instance.submit_time.astimezone(
                    to_tz)
                file_year, file_month, file_day = \
                    submit_time.year, submit_time.month, \
                    submit_time.day
                filename = old_file_path.split('/')[-1]
                new_url = f"{settings.STORAGE_LIST[0]}/dataqueue/" \
                    f"{file_year}/{file_month}/{file_day}/"
                check_folder = os.path.isdir(os.path.join(
                    settings.MEDIA_ROOT, new_url))
                if not check_folder:
                    os.makedirs(os.path.join(
                        settings.MEDIA_ROOT, new_url))
                shutil.move(
                    (os.path.join(
                        settings.MEDIA_ROOT, old_file_path)),
                    os.path.join(
                        settings.MEDIA_ROOT,
                        new_url + item + "_" + filename))

                update_url[item] = new_url + item + "_" + filename
    DataAnalysisQueue.objects.filter(pk=instance.pk).update(**update_url)


class SavedVisualization(models.Model):
    """used to describe saved Visualization."""
    visualization_app = models.ForeignKey(
        "VisualizationApp",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    data_source = models.ManyToManyField(DataAnalysisQueue)
    visualization_name = models.TextField(
        max_length=100, blank=True, null=True)
    last_saved = models.DateTimeField(blank=True, null=True)
    visual_creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.SET_NULL, blank=True,
                                       null=True)
    settings = models.JSONField(default=dict, null=True)


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True,
                             null=True)
    title = models.TextField(
        max_length=100, blank=True, null=True)
    content = models.TextField(
        max_length=10000, blank=True, null=True)
    stars = models.FloatField(blank=True, null=True)


class AppAuthor(models.Model):

    name = models.TextField(
        max_length=100, blank=True, null=True)
    description = models.TextField(
        max_length=10000, blank=True, null=True)
    url = models.TextField(
        max_length=500, blank=True, null=True)
    contact_email = models.TextField(
        max_length=500, blank=True, null=True)
    address = models.TextField(
        max_length=500, blank=True, null=True)
    image_link = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/images/",
        blank=True, null=True)


class ProcessingApp(models.Model):
    name = models.TextField(
        max_length=100, blank=True, null=True)
    version = models.TextField(
        max_length=100, blank=True, null=True)
    is_enabled = models.BooleanField(default=False, null=True)
    description = models.TextField(
        max_length=5000, blank=True, null=True)
    icon = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/images/",
        blank=True, null=True)
    install_package = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/codes/install",
        blank=True, null=True)
    process_package = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/codes/processing",
        blank=True, null=True)
    app_url = models.TextField(
        max_length=100, blank=True, null=True)
    preset_1 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}e/systemfiles/presets/",
        blank=True, null=True)
    preset_2 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_3 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_4 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_5 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_6 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_7 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_8 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_9 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    preset_10 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)

    app_author = models.ForeignKey(
        "AppAuthor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviews = models.ForeignKey(
        "Review",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )


class VisualizationApp(models.Model):
    name = models.TextField(
        max_length=100, blank=True, null=True)
    version = models.TextField(
        max_length=100, blank=True, null=True)
    is_enabled = models.BooleanField(default=False, null=True)
    description = models.TextField(
        max_length=5000, blank=True, null=True)
    icon = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/images/",
        blank=True, null=True)
    app_url = models.TextField(
        max_length=100, blank=True, null=True)
    support_process_apps = models.ManyToManyField(ProcessingApp, blank=True)
    app_author = models.ForeignKey(
        "AppAuthor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviews = models.ForeignKey(
        "Review",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
