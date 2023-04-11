"""
Define define the data models for the application. These data models describe
the structure of the data that will be stored in the application's database.
"""
# Standard library imports
import logging
import os
import random
import shutil
import string
import zipfile

# Third-party imports
from django.db import models
from django.utils import timezone
from django_currentuser.db.models import CurrentUserField

# Django imports
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# Local imports
from .File_converter import FileConverter


logger = logging.getLogger(__name__)
logger.info("Models reloaded")


class FileStorage(models.Model):
    """_used to save various file types_
    Args:
       file_type: 0: cache/pkl
            1-4 raw four different locations
            5 note files
            6-9 process file different locations
    """
    file_location = models.FileField(blank=True, null=True)
    file_type = models.TextField(max_length=10, blank=True, null=True)


class SampleRecord(models.Model):
    """This is the main class, used to describe a sample record
    """
    record_name = models.TextField(max_length=100, blank=True, null=True)
    record_description = models.TextField(
        max_length=1000, blank=True, null=True)
    file_vendor = models.TextField(
        max_length=20, blank=True, null=True)  # vendor and type
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
        upload_to="temp/", blank=True, null=True)
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
    project_name = models.TextField(max_length=50, blank=True, null=True)
    sample_type = models.TextField(max_length=10, blank=True, null=True)
    factor_1_name = models.TextField(max_length=20, blank=True, null=True)
    factor_1_value = models.TextField(
        max_length=10, blank=True, null=True)
    factor_2_name = models.TextField(max_length=20, blank=True, null=True)
    factor_2_value = models.TextField(
        max_length=10, blank=True, null=True)
    factor_3_name = models.TextField(max_length=20, blank=True, null=True)
    factor_3_value = models.TextField(
        max_length=10, blank=True, null=True)
    factor_4_name = models.TextField(max_length=20, blank=True, null=True)
    factor_4_value = models.TextField(
        max_length=10, blank=True, null=True)
    factor_5_name = models.TextField(max_length=20, blank=True, null=True)
    factor_5_value = models.TextField(
        max_length=10, blank=True, null=True)
    factor_6_name = models.TextField(max_length=20, blank=True, null=True)
    factor_6_value = models.TextField(
        max_length=10, blank=True, null=True)
    factor_7_name = models.TextField(max_length=20, blank=True, null=True)
    factor_7_value = models.TextField(
        max_length=10, blank=True, null=True)
    factor_8_name = models.TextField(max_length=20, blank=True, null=True)
    factor_8_value = models.TextField(
        max_length=10, blank=True, null=True)


@receiver(post_save, sender=SampleRecord, dispatch_uid="process uploaded file")
def process_uploaded(sender, instance, **kwargs):
    """procee the raw file once recrod created and file uploaded
    including file convertion, meta info extraction, flag: is_processed
    """
    if not instance.is_processed:
        logger.info("Start processing uploaded file")

        convert = FileConverter(
            instance,
            FileStorage,
            UserSettings.objects.filter(user=instance.record_creator))
        if convert.sucess:
            # Automatically create QC based on user settings(app/preset)
            if UserSettings.objects.filter(
                    user=instance.record_creator).first() is None:
                auto_qc = "None"
                workflow_tool_list = []
                save_qc_file = False
            else:
                user_setting = UserSettings.objects.filter(
                    user=instance.record_creator.pk).first(
                )
                auto_qc = user_setting.QC_tool
                save_qc_file = user_setting.save_qc_file
                workflow_tool_list = UserSettings.objects.filter(
                    user=instance.record_creator.pk).first(
                ).workflow_tool
            if auto_qc != "None":
                # auto_qc and workflow_tool format: app_pk+qc+qc_preset_number
                # for single run processing,
                # if last parameter isn ot  study_group.
                qc_setting_list = auto_qc.split("qc")
                # list item 1 is qc app pk, 2 is qc preset number

                all_records = []
                all_records.append(instance)

                qc_task = create_process_task(
                    qc_setting_list,
                    instance,
                    str(instance.pk)+"_QC",
                    all_records,
                    keep_full_output=save_qc_file)
                SampleRecord.objects.filter(pk=instance.pk).update(
                    quanlity_check=qc_task.pk)

            if workflow_tool_list and \
               instance.factor_8_name == "study_group" \
               and instance.factor_8_value[-4:] == "last":
                # for batch processing, factor_8 is study_group and it only
                # trigger when it is the last run of the study_group, value
                # end with last
                for item in workflow_tool_list:
                    worfkflow_setting_list = item.split("qc")

                    all_records = []
                    # batch run processing, same project, same study_group
                    project_name = instance.project_name
                    for item in SampleRecord.objects.filter(
                            project_name=project_name,
                            factor_8_value__contains=instance.factor_8_value[
                                :-4]):
                        all_records.append(item)

                    workflow_task = create_process_task(
                        worfkflow_setting_list,
                        instance,
                        project_name + "_" +
                        instance.factor_8_value[:-4]+"_" +
                        ProcessingApp.objects.filter(
                            pk=worfkflow_setting_list[0]).first().name,
                        all_records)
                    logger.info(
                        f"Batch process {workflow_task.pk} was created "
                        f"by {instance.record_creator}")

        logger.info(
            f"New sample record {instance.pk} was created "
            f"by {instance.record_creator}")

    SampleRecord.objects.filter(pk=instance.pk).update(
        is_processed=True)


def create_process_task(qc_setting_list, instance, task_name, record_list, keep_full_output=True):
    """_used to create analysis queue task based qc or workflow setting_
    Args:
        qc_setting_list (_list of number in str_): _[app_pk, qc_preset_number]_
        instance (_type_): _SampleRecrod instance_
        task_name (_type_): _task name_
        record_list (_type_): _list of sample record_
    Returns:
        DataAnalysisQueue: DataAnalysisQueue created
    """
    process_app = ProcessingApp.objects.filter(
        pk=qc_setting_list[0]).first()
    newqueue = {
        "processing_name": task_name,
        'processing_app': process_app,
        'process_creator': instance.record_creator,
        'keep_full_output': keep_full_output,
    }
    newtask = DataAnalysisQueue.objects.create(**newqueue, )
    # attach all the records into queue
    for item in record_list:
        newtask.sample_records.add(item)

    # attach preset input files into queue
    preset_file = os.path.join(
        settings.MEDIA_ROOT, getattr(
            process_app, f"preset_{qc_setting_list[1]}").name)
    with zipfile.ZipFile(preset_file, 'r') as z:
        for target_file in z.namelist():
            for n in range(1, 4):
                if target_file.startswith(f'input_file_{n}'):
                    path = z.extract(
                        target_file,
                        os.path.join(
                            settings.MEDIA_ROOT,
                            "primary_storage/"
                            "dataqueue/uniquetempfolder"))
                    setattr(
                        newtask, f"input_file_{n}", path)
    newtask.save()

    # TODO There is a race condition here, the task is created but not yet
    # processed by the auto_processing, the client processor can start before
    # the auto_processing is done. hopefully the auto_processing is fast.

    # if the processing app used by auto_qc or workflow_tool need
    # to be further processed, run auto_processing from the module
    module_name = process_app.progam_file_name
    if module_name not in dir():
        # if module has not already been imported
        string = \
            f'from file_manager.processing_apps' \
            f' import {module_name}'
        exec(string)
    # perform auto_processing if needed/available
    try:
        auto_process_string = \
            f"{module_name}.auto_processing (newtask.pk, preset_file)"
        exec(auto_process_string)
    except AttributeError:
        pass  # nothing need to be done here, no auto_processing needed
    except Exception as e:
        logger.error(
            f"Error in auto_processing for {newtask.pk}: {e}")
    return newtask


class UserSettings(models.Model):
    """_used to save user settings_
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True,
                             null=True)

    hide_othersresult = models.BooleanField(default=False, null=True)
    # formate for qc_pro_tool is process_app_pk + "qc" + preset_number
    QC_tool = models.TextField(
        max_length=10, blank=True, null=True, default="None")
    # qc_pro_tool used to process individual file for QC purpose
    workflow_tool = models.JSONField(null=True)
    # workflow_tool used to process group of files for the whole
    # list of workflows, same format as QC_tool
    qc_1_name = models.TextField(
        max_length=10, blank=True, null=True, default="Protein")
    qc_2_name = models.TextField(
        max_length=10, blank=True, null=True, default="Peptide")
    qc_3_name = models.TextField(
        max_length=10, blank=True, null=True, default="PSM")
    qc_4_name = models.TextField(
        max_length=10, blank=True, null=True, default="MS2")
    save_qc_file = models.BooleanField(default=False, null=True)
    # advanced setting, only accessible in the Django-admin Module
    conversion_settings = models.JSONField(
        default=settings.DEFAULT_MZML_CONVERSION_SETTING, null=True)
    replace_raw_with_mzML = models.BooleanField(default=False, null=True)

    def __str__(self):
        return 'Profile of user: {}'.format(self.user.username)


class SystemSettings(models.Model):
    """_system settings, four storages:primary_storage,secondary_storage,
    remote_storage, offline_storage, will be mounted through docker or
    ubuntu itself_
    """
    facility_name = models.TextField(
        max_length=20, blank=True, default="My", null=True)
    auto_backup_settings = models.JSONField(default=dict, null=True)
    auto_purge_settings = models.JSONField(default=dict, null=True)
    systemfile_backup_settings = models.JSONField(default=dict, null=True)
    system_version = models.TextField(
        max_length=10, blank=True, null=True)
    app_store_server = models.TextField(
        max_length=100,
        blank=True,
        default="https://proteomicsdata.com/",
        null=True)
    secret_mode = models.BooleanField(default=False, null=True)
    # user can only view their own file unless stuff if secret_mode is True


class WorkerStatus(models.Model):
    """_used to describe  data process queue._
    """
    processing_app = models.ForeignKey(
        "ProcessingApp",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    seq_number = models.IntegerField(blank=True, null=True, default=0)
    worker_ip = models.TextField(max_length=30, blank=True, null=True)
    worker_name = models.TextField(max_length=50, blank=True, null=True)
    last_update = models.TextField(max_length=50, blank=True, null=True)
    current_job = models.TextField(max_length=20, blank=True, null=True)


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
        max_length=50, blank=True, null=True)
    worker_hostname = models.TextField(
        max_length=50, blank=True, null=True)
    keep_full_output = models.BooleanField(default=True, null=True)
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
    output_file_4 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    output_file_5 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    output_file_6 = models.FileField(
        upload_to=(f"{settings.STORAGE_LIST[0]}/dataqueue/uniquetempfolder"),
        null=True, blank=True,)
    backup_indeces = models.ManyToManyField(
        FileStorage, related_name="procee_queue_backup", blank=True)
    output_QC_number_1 = models.IntegerField(blank=True, null=True)
    output_QC_number_2 = models.IntegerField(blank=True, null=True)
    output_QC_number_3 = models.IntegerField(blank=True, null=True)
    output_QC_number_4 = models.IntegerField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_finish_time = self.finish_time

    def save(self, *args, **kwargs):
        if self.finish_time != self._original_finish_time:
            # Perform any additional actions you'd like here
            pass
        super().save(*args, **kwargs)
        self._original_finish_time = self.finish_time


@ receiver(post_save, sender=DataAnalysisQueue, dispatch_uid="move files")
def move_file(sender, instance, **kwargs):
    """_process the uploaded files
        1. move files to year/month/date folders
        2. process the results files according to the process apps_
    """
    update_url = {}

    for item in settings.PROCESS_FILE_LIST:
        old_file_path = getattr(instance, item).name
        if old_file_path:
            if "uniquetempfolder" in old_file_path:
                to_tz = timezone.get_default_timezone()
                submit_time = instance.submit_time.astimezone(
                    to_tz)
                file_year, file_month, file_day = \
                    submit_time.year, submit_time.month, \
                    submit_time.day
                filename = os.path.basename(old_file_path)
                new_url = f"{settings.STORAGE_LIST[0]}/dataqueue/" \
                    f"{file_year}/{file_month}/{file_day}/{instance.pk}/"
                check_folder = os.path.isdir(os.path.join(
                    settings.MEDIA_ROOT, new_url))
                if not check_folder:
                    os.makedirs(os.path.join(
                        settings.MEDIA_ROOT, new_url))
                if os.path.exists(os.path.join(
                        settings.MEDIA_ROOT,
                        new_url + filename)):
                    random_str = "".join(random.choice(
                        string.ascii_lowercase) for i in range(4))
                    root_ext = os.path.splitext(filename)
                    filename = root_ext[0] + f"_{random_str}"+root_ext[1]
                shutil.move(
                    (os.path.join(
                        settings.MEDIA_ROOT, old_file_path)),
                    (os.path.join(
                        settings.MEDIA_ROOT, new_url + filename))
                )
                update_url[item] = new_url + filename
    DataAnalysisQueue.objects.filter(pk=instance.pk).update(**update_url)

    if instance.finish_time != instance._original_finish_time:
        # perform process app's post_processing  if finish_time is updated
        module_name = instance.processing_app.progam_file_name

        if module_name not in dir():
            # if module has not already been imported
            import_string = \
                f'from file_manager.processing_apps' \
                f' import {module_name}'
            exec(import_string)
    # perform auto_processing if needed/available
        try:
            auto_process_string = \
                f"{module_name}.post_processing(instance.pk)"
            exec(auto_process_string)
        except AttributeError:
            pass  # nothing need to be done here, no auto_processing needed
        except Exception as e:
            logger.error(
                f"Error in post_processing for {instance.pk}: {e}")


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
        max_length=50, blank=True, null=True)
    last_saved = models.DateTimeField(blank=True, null=True)
    visual_creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.SET_NULL, blank=True,
                                       null=True)
    settings = models.JSONField(default=dict, null=True)


class ProcessingApp(models.Model):
    """used to describe processing app."""
    name = models.TextField(
        max_length=30, blank=True, null=True)
    installed_version = models.TextField(
        max_length=10, blank=True, null=True)
    is_enabled = models.BooleanField(default=False, null=True)
    description = models.TextField(
        max_length=500, blank=True, null=True)
    icon = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/images/",
        blank=True, null=True)
    install_package = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/codes/install",
        blank=True, null=True)
    process_package = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/codes/processing",
        blank=True, null=True)
    app_homepage_url = models.TextField(
        max_length=100, blank=True, null=True)
    preset_1 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
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
    user_preset_1 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    user_preset_2 = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/presets/",
        blank=True, null=True)
    app_author = models.TextField(
        max_length=20, blank=True, null=True)
    last_install = models.DateTimeField(blank=True, null=True)
    downloaded_version = models.TextField(
        max_length=20, blank=True, null=True)
    is_installed = models.BooleanField(default=False, null=True)
    # how to generate import uuid; uuid.uuid4().hex.upper()[0:12]
    UUID = models.TextField(
        max_length=50, blank=True, null=True)  # used for server side ID
    progam_file_name = models.TextField(
        max_length=20, blank=True, null=True)
    # progam_file_name must match module main py name


class VisualizationApp(models.Model):
    """used to describe visualization app."""
    name = models.TextField(
        max_length=50, blank=True, null=True)
    installed_version = models.TextField(
        max_length=20, blank=True, null=True)
    is_enabled = models.BooleanField(default=False, null=True)
    description = models.TextField(
        max_length=500, blank=True, null=True)
    install_package = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/codes/install",
        blank=True, null=True)
    icon = models.FileField(
        upload_to=f"{settings.STORAGE_LIST[0]}/systemfiles/images/",
        blank=True, null=True)
    app_homepage_url = models.TextField(
        max_length=50, blank=True, null=True)
    support_process_apps = models.TextField(
        max_length=100, blank=True, null=True)
    app_author = models.TextField(
        max_length=20, blank=True, null=True)
    last_install = models.DateTimeField(blank=True, null=True)
    downloaded_version = models.TextField(
        max_length=20, blank=True, null=True)
    is_installed = models.BooleanField(default=False, null=True)
    UUID = models.TextField(
        max_length=50, blank=True, null=True)
    progam_file_name = models.TextField(
        max_length=20, blank=True, null=True)
    # progam_file_name must match module main py name
