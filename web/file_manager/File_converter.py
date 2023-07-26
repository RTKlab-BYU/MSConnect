"""
Define how raw files are converted to mzML files, and how the data is extracted
and cached and moved to the correct location.
"""
# Standard library imports
import datetime
import logging
import os
import random
import shutil
import string
import time
import xmltodict
# Third-party imports
import pickle
from python_on_whales import docker
from zipfile import ZipFile
import xml.sax
from collections import deque

# Django imports
from django.conf import settings
from django.utils import timezone
from .XMLReader import CustomContentHandler
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)


class FileConverter():
    """convert the passed SampleRecord istance and covernt the file, extract
    data
    """

    def __init__(self, instance=None, FileStorage=None, creator_setting=None, system_setting=None):
        self.record = instance
        self.sucess = False
        self.filestorage = FileStorage
        self.creator_setting = creator_setting
        self.system_setting = system_setting
        self.filename = os.path.splitext(instance.temp_rawfile.name)[
            0].split('/')[-1]
        self.extension = os.path.splitext(self.record.temp_rawfile.name)[1][1:]
        self.fullname = self.filename + "." + self.extension
        # unpack the content in the string of project_name in the formate of
        #  "project_name, enablebatch(True or False), txtbatchname, userslist"
        self.record.project_name, self.enable_batch, self.batch_name,\
            self.assigned_user = self.record.project_name.split(',')
        try:
            self.assigned_user = int(self.assigned_user)
        except Exception as error:  # not a user
            pass
        else:
            if self.record.record_creator.is_staff and self.assigned_user != 0:
                self.record.record_creator = User.objects.get(
                    pk=self.assigned_user)
        to_tz = timezone.get_default_timezone()
        self.record.acquisition_time = self.record.uploaded_time
        # compromise, otherwise on acquisition time for sort
        upload_time = self.record.uploaded_time.astimezone(
            to_tz)
        self.file_year, self.file_month, self.file_day = \
            upload_time.year, upload_time.month, \
            upload_time.day
        self.mzML = os.path.join(
            settings.MEDIA_ROOT,
            f'{os.path.splitext(self.record.temp_rawfile.name)[0]}'
            '.mzML')

        try:
            if self.creator_setting.exists() and \
                    self.creator_setting.first().perform_extraction:
                if self.convert():
                    self.create_cache()
        except Exception as err:
            logger.error(f"During convert and cache creation, {err}")
        finally:
            self.move_file()
            self.record.is_processed = True
            self.record.save()

    def convert(self):
        """Convert the uploaded file to mzml format with metadata.json, extract
        meta data
        return True if finished properly (geneated metadata.json file)
        """

        temp_file = os.path.join(
            settings.MEDIA_ROOT, self.record.temp_rawfile.name)
        self.record.file_size = os.path.getsize(temp_file)/1024/1024/1024
        if self.extension == "zip":
            with ZipFile(temp_file, 'r') as f:
                f.extractall(os.path.dirname(temp_file) + f"/{self.filename}/")
            conversion_file = self.filename
        else:
            conversion_file = self.fullname

        # check if the creator has a custom docker conversion setting, if not
        # use the default setting from settings.py
        if self.creator_setting.exists() and \
                self.creator_setting.first().conversion_settings != "":
            converter_image = \
                self.creator_setting.first(
                ).conversion_settings["docker_image"]
            converter_cmd = \
                self.creator_setting.first().conversion_settings[
                    "command_list_before_file"] + [
                    f"/data/{conversion_file}"] + \
                self.creator_setting.first(
                ).conversion_settings["command_list_after_file"]
        else:
            converter_image = \
                settings.DEFAULT_MZML_CONVERSION_SETTING["docker_image"]
            converter_cmd = \
                settings.DEFAULT_MZML_CONVERSION_SETTING[
                    "command_list_before_file"] + [
                    f"/data/{conversion_file}"] + \
                settings.DEFAULT_MZML_CONVERSION_SETTING[
                    "command_list_after_file"]
        docker_sucess = False
        retry_dock = 0
        while not docker_sucess and retry_dock < 3:  # max retry docker
            try:
                if "is_docker" in os.environ:
                    # running inside docker containner, docker in docker case
                    # normal deployment case
                    output = docker.run(
                        converter_image,
                        converter_cmd,
                        volumes=[("/var/temp", "/data")],
                        interactive=True,
                        remove=True,
                    )
                else:  # not inside containner, debug mode
                    output = docker.run(
                        converter_image,
                        converter_cmd,
                        volumes=[(os.path.dirname(temp_file), "/data")],
                        interactive=True,
                        remove=True,
                    )
                self.mzML = os.path.join(
                    settings.MEDIA_ROOT,
                    f"{os.path.dirname(temp_file)}/"
                    f"{conversion_file.split('.')[0]}"
                    f".mzML"
                )
                logger.info(f"Docker conversion finished, {output}")
            except Exception as error:
                logger.error(f"During Docker process for conversion,"
                             f" this is {retry_dock} try {error}")
                os.remove(self.mzML)
            time.sleep(5)
            if os.path.exists(self.mzML):
                docker_sucess = True
            else:
                retry_dock += 1
        if os.path.exists(self.mzML):
            return True
        else:
            self.record.notes = "Raw file extraction failed "
            logger.error("No mzML file was found after conversion")
            return False

    def create_cache(self):
        """_Create pkl cache file from mzMl for display_
        """
        retry = 0
        is_converted = False
        # file conversion fails sometimes, a re-try upto 6 time was used
        while (retry < settings.FILE_CONVERT_RETRY and not is_converted):
            try:
                xml_parse = CustomContentHandler()
                xml.sax.parse(self.mzML, xml_parse)
            except Exception as error:
                logger.warning(f"Convertion failed {retry+1} time, "
                               f"will retry until failed 6 times, {error}")
                os.remove(self.mzML) if os.path.exists(self.mzML) else None
                time.sleep(10)
                self.convert()
            else:
                is_converted = True
            finally:
                retry = retry + 1
                if retry >= settings.FILE_CONVERT_RETRY and not is_converted:
                    logger.error(
                        f"{self.fullname} Convertion "
                        f"abandoned after {retry} retries.")
                    return False
        if not self.creator_setting.exists() or \
                not self.creator_setting.first().replace_raw_with_mzML:
            os.remove(self.mzML) if os.path.exists(self.mzML) else None

        self.record.instrument_model = xml_parse.model
        self.record.instrument_sn = xml_parse.SN
        self.record.acquisition_time = xml_parse.acquisition_time

        self.file_year, self.file_month, self.file_day = \
            self.record.acquisition_time.year, \
            self.record.acquisition_time.month, \
            self.record.acquisition_time.day

        plot_data = {"MS1_RT": xml_parse.ms1_rt,
                     "MS1_Basemzintensity": xml_parse.ms1_basemzintensity,
                     "MS1_Ticintensity": xml_parse.ms1_ticintensity,
                     "MS2_RT": xml_parse.ms2_rt,
                     "MS2_Injectiontime": xml_parse.ms2_injectiontime}
        pkl_location = f"primary_storage/pkl/{self.file_year}/" \
            f"{self.file_month}/{self.file_day}/"\
            f"{self.filename}.pkl"

        file_dir = os.path.dirname(os.path.join(
            settings.MEDIA_ROOT, pkl_location))
        check_folder = os.path.isdir(
            os.path.join(settings.MEDIA_ROOT, file_dir))
        if not check_folder:
            os.makedirs(file_dir)
        with open(os.path.join(settings.MEDIA_ROOT,
                               pkl_location), "wb") as handle:
            pickle.dump(plot_data, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)
        FileStorageform = {
            "file_location": pkl_location,
            "file_type": 0
        }
        pklobj = self.filestorage.objects.create(**FileStorageform, )
        self.record.cache_pkl = pklobj
        return True

    def move_file(self):
        """_Move the file to the right location and save related info_
        """
        # separate file by group if enabled by admin

        try:
            group_name = self.record.record_creator.groups.all()[0]
        except Exception as error:
            group_name = "others"
        if "enabled_group_folder" in \
                self.system_setting.other_settings.keys() and \
                self.system_setting.other_settings[
                        "enabled_group_folder"] == "TRUE":
            if self.enable_batch == "True" and self.batch_name != "":
                file_dir = f"primary_storage/rawfiles/{group_name}/"\
                    f"{self.record.record_creator}/" \
                    f"{self.record.project_name}/{self.batch_name}/"
            else:
                file_dir = f"primary_storage/rawfiles/{group_name}/"\
                    f"{self.record.record_creator}/" \
                    f"{self.record.project_name}/"

        else:  # separate file by month without group and user
            if self.enable_batch == "True" and self.batch_name != "":
                file_dir = f"primary_storage/rawfiles/{self.file_year}/"\
                    f"{self.file_month}/{self.record.project_name}/{self.batch_name}/"
            else:
                file_dir = f"primary_storage/rawfiles/{self.file_year}/"\
                    f"{self.file_month}/{self.record.project_name}/"
        check_folder = os.path.isdir(os.path.join(
            settings.MEDIA_ROOT, file_dir))
        if not check_folder:
            os.makedirs(os.path.join(
                settings.MEDIA_ROOT, file_dir))
        # keep the original raw file or converted mzML file
        if self.creator_setting.exists() and \
                self.creator_setting.first().replace_raw_with_mzML:
            newfile_name = f"{file_dir}/{self.filename + '.mzML'}"
            if os.path.exists(os.path.join(
                    settings.MEDIA_ROOT, newfile_name)):
                random_str = "".join(random.choice(
                    string.ascii_lowercase) for i in range(4))
                newfile_name = (f"{file_dir}/"
                                f"{self.filename}"
                                f"_{random_str}.mzML")
            os.remove((os.path.join(
                settings.MEDIA_ROOT, self.record.temp_rawfile.name)))
            shutil.move(
                self.mzML,
                os.path.join(
                    settings.MEDIA_ROOT, newfile_name))
        else:
            newfile_name = f"{file_dir}/{self.fullname}"
            if os.path.exists(os.path.join(
                    settings.MEDIA_ROOT, newfile_name)):
                random_str = "".join(random.choice(
                    string.ascii_lowercase) for i in range(4))
                newfile_name = (f"{file_dir}/"
                                f"{self.filename}"
                                f"_{random_str}.{self.extension}")
            shutil.move(
                (os.path.join(
                    settings.MEDIA_ROOT, self.record.temp_rawfile.name)),
                os.path.join(
                    settings.MEDIA_ROOT, newfile_name))
        self.record.file_size = os.path.getsize(os.path.join(
            settings.MEDIA_ROOT, newfile_name))/1024/1024/1024
        FileStorageform = {
            "file_location": newfile_name,
            "file_type": 1
        }
        saved_storage = self.filestorage.objects.create(
            **FileStorageform, )
        self.record.file_storage_indeces.add(saved_storage)
        self.record.newest_raw = saved_storage
        self.record.temp_rawfile = None
        self.sucess = True
