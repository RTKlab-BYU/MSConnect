from django.db import models
from django.conf import settings
from datetime import date
import datetime
import xmltodict

from django_currentuser.db.models import CurrentUserField
from django.contrib.contenttypes.models import ContentType

import pickle
import os
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


class NoteFile(models.Model):
    notefile = models.FileField(upload_to=f"notefiles/{date.today().year}/ \
        {date.today().month}/{date.today().day}", blank=True, null=True)


class SsdStorage(models.Model):
    filelocation = models.FileField(upload_to="temp/", blank=True, null=True)


class HdStorage(models.Model):
    filelocation = models.FileField(blank=True, null=True)


class RemoteStorage(models.Model):
    filelocation = models.FileField(blank=True, null=True)


class OfflineStorage(models.Model):
    filelocation = models.FileField(blank=True, null=True)


class PklStorage(models.Model):
    filelocation = models.FileField(blank=True, null=True)


class RawFile(models.Model):
    """This is the main class, used to describe a MS run
    """
    run_name = models.TextField(max_length=100, blank=True, null=True)
    plot_label = models.TextField(max_length=100, blank=True, null=True)
    project_name = models.TextField(max_length=100, blank=True, null=True)
    run_desc = models.TextField(max_length=1000, blank=True, null=True)
    qc_tool = models.IntegerField(blank=True, null=True, default=0)
    qc_mbr = models.TextField(max_length=1000, blank=True, null=True)
    instrument_model = models.TextField(max_length=100, blank=True, null=True)
    instrument_sn = models.TextField(max_length=100, blank=True, null=True)
    creator = CurrentUserField()
    notes = models.TextField(max_length=1000, blank=True, null=True)
    note_file = models.ManyToManyField(NoteFile, blank=True)
    temp_data = models.BooleanField(default=False, null=True)
    sample_obj = models.IntegerField(blank=True, null=True, default=0)
    column_sn = models.TextField(max_length=100, blank=True, null=True)
    spe_sn = models.TextField(max_length=100, blank=True, null=True)
    rawfile = models.FileField(upload_to="temp/", blank=True, null=True)
    storage_option = models.IntegerField(blank=True, null=True, default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    acquisition_time = models.DateTimeField(blank=True, null=True)
    sample_type = models.TextField(max_length=100, blank=True, null=True)
    pklfile = models.FileField(null=True, blank=True,)
    file_size = models.DecimalField(default=0, max_digits=5,
                                    decimal_places=3, blank=True, null=True)
    content_extracted = models.BooleanField(default=False, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT,
                                     null=True, blank=True,)
    object_id = models.PositiveIntegerField(default=5)
    current_raw = fields.GenericForeignKey(
        "content_type", "object_id")

    ssd_storage = models.ForeignKey(
        "SsdStorage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    hd_storage = models.ForeignKey(
        "HdStorage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    remote_storage = models.ForeignKey(
        "RemoteStorage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    offline_storage = models.ForeignKey(
        "OfflineStorage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    pkl_storage = models.ForeignKey(
        "PklStorage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    qc_content_type = models.ForeignKey(
        ContentType, related_name="qc_content", on_delete=models.PROTECT,
        null=True, blank=True,)
    qc_object_id = models.PositiveIntegerField(default=1)
    current_qc = fields.GenericForeignKey(
        "qc_content_type", "qc_object_id")


# TODO:remove pklfile field, replace with pkl_storage, should be very easy.


@receiver(post_save, sender=RawFile, dispatch_uid="update and move the file")
def update_raw(sender, instance, **kwargs):
    """Perform file convertion, meta info extraction when save a new record
    """
    # TODO: add error handling if can"t convert file or read file

    if not instance.content_extracted:
        # for Thermo raw files
        if instance.rawfile.name.split(".")[-1] == "raw":
            rawfile_name = instance.rawfile.name
            rawfile_name_only = rawfile_name.split("/")[-1]
            try:
                """
                have to do this batch approach as the following directly mono
                command approch (tried 5 hours) won't work result = subprocess.
                run(['mono',f'/home/rtklab/Documents/data_manager/
                ThermoRawFileParser/ThermoRawFileParser.exe
                -i=/home/rtklab/Documents/data_manager/media/{rawfile_name}
                 -m=0'], capture_output=True)
                """
                batch_file = open("ThermoRawFileParser/run.sh", "w")
                batch_file.write(" #!/bin/bash \n")
                command_1 = "mono /home/rtklab/Documents/data_manager/"\
                    "ThermoRawFileParser/ThermoRawFileParser.exe "\
                    "-d=/home/rtklab/Documents/data_manager/media/temp"\
                    "  -m=0  -f=1 -L=1,2"
                batch_file.write(command_1)
                batch_file.close()
                command_2 = "/home/rtklab/Documents/data_manager/"\
                    "ThermoRawFileParser/run.sh"
                result = subprocess.run(
                    ["sh", command_2], capture_output=True)
                print(result)
                time.sleep(1)
                filename = os.path.join(
                    "/home/rtklab/Documents/data_manager/media/temp/",
                    rawfile_name_only[:-4]+"-metadata.json")
                f = open(filename,)
                data = json.load(f)
                f.close()
                os.remove(filename)
                RawFile.objects.filter(pk=instance.pk).update(
                    acquisition_time=datetime.datetime.strptime(
                        data["FileProperties"][2]["value"],
                        "%m/%d/%Y %H:%M:%S"))
                RawFile.objects.filter(pk=instance.pk).update(
                    instrument_model=data["InstrumentProperties"][0]["value"])
                RawFile.objects.filter(pk=instance.pk).update(
                    instrument_sn=data["InstrumentProperties"][2]["value"])
                RawFile.objects.filter(pk=instance.pk).update(
                    sample_type=data["SampleData"][0]["value"])
                to_tz = timezone.get_default_timezone()
                file_year, file_month, file_date = RawFile.objects.\
                    filter(pk=instance.pk)[
                        0].acquisition_time.astimezone(to_tz).year,\
                    RawFile.objects.filter(pk=instance.pk)[
                        0].acquisition_time.astimezone(
                            to_tz).month, RawFile.objects.filter(
                        pk=instance.pk)[0].acquisition_time.astimezone(
                            to_tz).day
                if instance.project_name != "":
                    file_dir = os.path.join(
                        settings.MEDIA_ROOT,
                        (f"rawfiles/{file_year}/"
                         f"{file_month}/{instance.project_name}/"))
                else:
                    file_dir = os.path.join(
                        settings.MEDIA_ROOT,
                        f"rawfiles/{file_year}/{file_month}/{file_date}/")
                check_folder = os.path.isdir(file_dir)
                if not check_folder:
                    os.makedirs(file_dir)
                newfile_name = f"{file_dir}/{rawfile_name_only}"
                if exists(newfile_name):
                    random_str = "".join(random.choice(
                        string.ascii_lowercase) for i in range(4))
                    newfile_name = (f"{file_dir}/"
                                    f"{rawfile_name_only.split('.')[0]}"
                                    f"_{random_str}.raw")

                shutil.move(
                    (f"/home/rtklab/Documents/"
                     f"data_manager/media/temp/{rawfile_name_only}"),
                    newfile_name)

                # create the SsdStorage and point current to it
                if instance.project_name != "":
                    ssd_filelocation = (f"rawfiles/{file_year}/{file_month}/"
                                        f"{instance.project_name}/"
                                        f"{newfile_name.split('/')[-1]}")
                else:
                    ssd_filelocation = (f"rawfiles/{file_year}/{file_month}"
                                        f"/{file_date}/"
                                        f"{newfile_name.split('/')[-1]}")
                ssdform = {
                    "filelocation": ssd_filelocation
                }
                ssdob = SsdStorage.objects.create(**ssdform, )

                RawFile.objects.filter(
                    pk=instance.pk).update(ssd_storage=ssdob)
                RawFile.objects.filter(pk=instance.pk).update(
                    rawfile=ssdob.filelocation)

                #
                ct = ContentType.objects.get_for_model(SsdStorage)
                RawFile.objects.filter(pk=instance.pk).update(
                    content_type=ct, object_id=ssdob.pk)

                ssdfilename = os.path.join(
                    settings.MEDIA_ROOT, ssd_filelocation)

                filenamelen = len(ssd_filelocation.split("/")[-1])
                des_path = (f"media/hdstorage/"
                            f"{ssd_filelocation[:filenamelen*-1]}")
                isExist = os.path.exists(des_path)
                if not isExist:
                    # Create a new directory because it does not exist
                    os.makedirs(des_path)
                shutil.copy(ssdfilename, des_path)
                hd_filelocation = f"hdstorage/{ssd_filelocation}"
                hdform = {
                    "filelocation": hd_filelocation
                }
                hdob = HdStorage.objects.create(**hdform, )

                RawFile.objects.filter(pk=instance.pk).update(hd_storage=hdob)

                file_size = os.path.getsize(
                    os.path.join(settings.MEDIA_ROOT, RawFile.objects.filter(
                        pk=instance.pk)[
                            0].current_raw.filelocation.name))/1024/1024/1024
                RawFile.objects.filter(pk=instance.pk).update(
                    file_size=file_size)

                # auto create QC SpectromineQueue
                # for some reason app and webiste generate different bool :(,
                #  need to happen before content extraction as
                # sometimes extraction may fail

                if (instance.qc_tool != "0" and instance.qc_tool != 0):
                    if (instance.qc_tool == "1" or instance.qc_tool == 1):
                        new_queue = {
                            "creator": instance.creator,
                        }
                        new_queue_obj = MsfraggerQueue.objects.create(
                            **new_queue, )
                        new_queue_obj.rawfile.add(
                            RawFile.objects.filter(pk=instance.pk).first())
                        new_queue_obj.save()

                        ct = ContentType.objects.get_for_model(MsfraggerQueue)
                        RawFile.objects.filter(
                            pk=instance.pk).update(qc_content_type=ct)
                        RawFile.objects.filter(pk=instance.pk).update(
                            qc_object_id=new_queue_obj.pk)
                    elif (instance.qc_tool == "3" or instance.qc_tool == 3):
                        # 3 is protein discoverer
                        new_queue = {
                            "creator": instance.creator,
                        }
                        new_queue_obj = PdQueue.objects.create(**new_queue, )
                        new_queue_obj.rawfile.add(
                            RawFile.objects.filter(pk=instance.pk).first())
                        new_queue_obj.save()

                        ct = ContentType.objects.get_for_model(PdQueue)
                        RawFile.objects.filter(
                            pk=instance.pk).update(qc_content_type=ct)
                        RawFile.objects.filter(pk=instance.pk).update(
                            qc_object_id=new_queue_obj.pk)

                # extract the mzML
                mzml_filename = rawfile_name_only[:-4]+".mzML"

                # defining an xml string
                with open(os.path.join("media/temp", mzml_filename),
                          "r") as xml_obj:
                    # coverting the xml data to Python dictionary
                    my_dict = xmltodict.parse(xml_obj.read())
                xml_obj.close()
                os.remove(os.path.join("media/temp", mzml_filename))
                ms1_rt = []
                ms1_basemz = []
                ms1_basemzintensity = []
                ms1_ticintensity = []
                ms2_rt = []
                ms2_injectiontime = []

                for i in range(0, len(my_dict["mzML"]["run"]
                                      ["spectrumList"]["spectrum"])):
                    if my_dict["mzML"]["run"][
                            "spectrumList"]["spectrum"][i]["cvParam"][0][
                                "@value"] == "1":
                        ms1_rt.append(float(my_dict["mzML"]["run"][
                            "spectrumList"]["spectrum"][i]["scanList"][
                                "scan"]["cvParam"][0]["@value"]))
                        ms1_basemz.append(round(float(
                            my_dict["mzML"]["run"]["spectrumList"][
                                "spectrum"][i]["cvParam"][5]["@value"]), 2))
                        ms1_basemzintensity.append(float(
                            my_dict["mzML"]["run"][
                                "spectrumList"]["spectrum"][i][
                                    "cvParam"][6]["@value"]))
                        ms1_ticintensity.append(float(
                            my_dict["mzML"]["run"]["spectrumList"][
                                "spectrum"][i]["cvParam"][3]["@value"]))
                    if my_dict["mzML"]["run"]["spectrumList"][
                            "spectrum"][i]["cvParam"][0]["@value"] == "2":
                        ms2_rt.append(float(my_dict["mzML"][
                            "run"]["spectrumList"]["spectrum"][i][
                                "scanList"]["scan"]["cvParam"][0]["@value"]))
                        ms2_injectiontime.append(float(
                            my_dict["mzML"]["run"]["spectrumList"][
                                "spectrum"][i]["scanList"]["scan"][
                                    "cvParam"][2]["@value"]))

                plot_data = {"MS1_RT": ms1_rt,
                             "MS1_Basemz": ms1_basemz,
                             "MS1_Basemzintensity": ms1_basemzintensity,
                             "MS1_Ticintensity": ms1_ticintensity,
                             "MS2_RT": ms2_rt,
                             "MS2_Injectiontime": ms2_injectiontime}

                newurl = RawFile.objects.filter(pk=instance.pk)[
                    0].rawfile.name.replace(".raw", ".pkl")
                outputfilename = os.path.join(settings.MEDIA_ROOT, newurl)
                with open(outputfilename, "wb") as handle:
                    pickle.dump(plot_data, handle,
                                protocol=pickle.HIGHEST_PROTOCOL)
                RawFile.objects.filter(pk=instance.pk).update(pklfile=newurl)

                pklform = {
                    "filelocation": newurl
                }
                pklobj = PklStorage.objects.create(**pklform, )

                RawFile.objects.filter(
                    pk=instance.pk).update(pkl_storage=pklobj)
                RawFile.objects.filter(pk=instance.pk).update(
                    content_extracted=True)
            except Exception as err:
                exception_type = type(err).__name__
                print(exception_type)
                instance.note = "Raw file extraction failed"

        else:
            instance.note = "Not valid data file type"


class SpectromineQueue(models.Model):
    """used to describe spectromine queue."""
    rawfile = models.ForeignKey(
        "RawFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    run_status = models.BooleanField(default=False, null=True)
    protein_id = models.IntegerField(blank=True, null=True)
    peptide_id = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    finished_time = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL, blank=True,
                                null=True)
    result_file = models.FileField(
        upload_to=(f"hdstorage/spectromine/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)

    def save(self, *args, **kwargs):
        super(SpectromineQueue, self).save(*args, **kwargs)
        if self.protein_id is not None:
            RawFile.objects.filter(pk=self.rawfile.pk).update(
                lastqc_protein_id=self.protein_id,
                lastqc_peptide_id=self.peptide_id,
                lastqc_tool="Spectromine", lastqc_time=datetime.datetime.now())


class SpectromineWorker(models.Model):
    """used to describe data process worker."""
    worker_name = models.TextField(max_length=100, blank=True, null=True)
    worker_ip = models.TextField(max_length=100, blank=True, null=True)
    worker_status = models.TextField(max_length=100, blank=True, null=True)
    current_job = models.ForeignKey(
        "SpectromineQueue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    current_percentage = models.IntegerField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)


class MaxquantQueue(models.Model):
    """used to describe Maxquant queue."""
    rawfile = models.ManyToManyField(RawFile)
    analysis_name = models.TextField(max_length=100, blank=True, null=True)
    setting_xml = models.FileField(
        upload_to=(f"maxquant_xml/{date.today().year}/{date.today().month}/"
                   f"{date.today().day}"), null=True, blank=True,)
    evidence_file = models.FileField(
        upload_to=(f"hdstorage/maxquant/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    protein_file = models.FileField(
        upload_to=(f"hdstorage/maxquant/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    peptide_file = models.FileField(
        upload_to=(f"hdstorage/maxquant/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    other_file = models.FileField(
        upload_to=(f"hdstorage/maxquant/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    run_status = models.BooleanField(default=False, null=True)
    protein_id = models.IntegerField(blank=True, null=True)
    peptide_id = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    finished_time = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL, blank=True,
                                null=True)


class MaxquantWorker(models.Model):
    """used to describe maxquant data process worker."""
    worker_name = models.TextField(max_length=100, blank=True, null=True)
    worker_ip = models.TextField(max_length=100, blank=True, null=True)
    worker_status = models.TextField(max_length=100, blank=True, null=True)
    current_job = models.ForeignKey(
        "MaxquantQueue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    current_percentage = models.IntegerField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)


class MsfraggerQueue(models.Model):
    """used to describe  Msfragger queue."""
    rawfile = models.ManyToManyField(RawFile)
    analysis_name = models.TextField(max_length=100, blank=True, null=True)
    ion_file = models.FileField(
        upload_to=(f"hdstorage/msfragger/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    psm_file = models.FileField(
        upload_to=(f"hdstorage/msfragger/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    peptide_file = models.FileField(
        upload_to=(f"hdstorage/msfragger/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    protein_file = models.FileField(
        upload_to=(f"hdstorage/msfragger/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)

    run_status = models.BooleanField(default=False, null=True)
    precurosr_id = models.IntegerField(blank=True, null=True)
    psm_id = models.IntegerField(blank=True, null=True)
    peptide_id = models.IntegerField(blank=True, null=True)
    protein_id = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    finished_time = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL, blank=True,
                                null=True)


class MsfraggerWorker(models.Model):
    """used to describe  Msfragger data process worker."""
    worker_name = models.TextField(max_length=100, blank=True, null=True)
    worker_ip = models.TextField(max_length=100, blank=True, null=True)
    worker_status = models.TextField(max_length=100, blank=True, null=True)
    current_job = models.ForeignKey(
        "MsfraggerQueue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    current_percentage = models.IntegerField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)


class PdQueue(models.Model):
    """used to describe ProteinDiscoverer queue."""
    rawfile = models.ManyToManyField(RawFile)
    analysis_name = models.TextField(max_length=100, blank=True, null=True)

    processing_method = models.FileField(
        upload_to=(f"hdstorage/proteindiscoverer/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    consensus_method = models.FileField(
        upload_to=(f"hdstorage/proteindiscoverer/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    result_file = models.FileField(
        upload_to=(f"hdstorage/proteindiscoverer/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    export_file = models.FileField(
        upload_to=(f"hdstorage/proteindiscoverer/{date.today().year}/"
                   f"{date.today().month}/{date.today().day}"),
        null=True, blank=True,)
    keep_result = models.BooleanField(default=False, null=True)
    TMT = models.IntegerField(blank=True, null=True)
    run_status = models.BooleanField(default=False, null=True)
    precurosr_id = models.IntegerField(blank=True, null=True)
    psm_id = models.IntegerField(blank=True, null=True)
    peptide_id = models.IntegerField(blank=True, null=True)
    protein_id = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    finished_time = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL, blank=True,
                                null=True)


class PdWorker(models.Model):
    """used to describe ProteinDiscoverer data process worker."""
    worker_name = models.TextField(max_length=100, blank=True, null=True)
    worker_ip = models.TextField(max_length=100, blank=True, null=True)
    worker_status = models.TextField(max_length=100, blank=True, null=True)
    current_job = models.ForeignKey(
        "PdQueue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    last_update = models.DateTimeField(blank=True, null=True)
