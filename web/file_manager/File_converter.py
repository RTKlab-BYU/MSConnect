import os
import subprocess
import time
import json
import datetime
from django.utils import timezone
import xmltodict
import pickle
import shutil
import random
import string
from django.conf import settings
<<<<<<< HEAD
=======
from python_on_whales import docker
from zipfile import ZipFile
import logging
logger = logging.getLogger(__name__)
>>>>>>> adding_process_node


class FileConverter():
    """convert the passed SampleRecord istance and covernt the file, extract
    data
    """

<<<<<<< HEAD
    def __init__(self, instance=None, FileStorage=None):
        self.record = instance
        self.sucess = False
        self.filestorage = FileStorage
=======
    def __init__(self, instance=None, FileStorage=None, creator_setting=None):
        self.record = instance
        self.sucess = False
        self.filestorage = FileStorage
        self.creator_setting = creator_setting
>>>>>>> adding_process_node

        self.filename = os.path.splitext(instance.temp_rawfile.name)[
            0].split('/')[-1]
        self.extension = os.path.splitext(self.record.temp_rawfile.name)[1][1:]
        self.fullname = self.filename + "." + self.extension
<<<<<<< HEAD
        self.file_year = 0
        self.file_month = 0
        self.file_day = 0

        if eval('self.' + self.extension + '()'):
            if self.create_cache():
                self.move_file()

        # self.sucess = True
        self.record.is_processed = True
        self.record.save()

    def raw(self):
=======

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

<<<<<<< HEAD
        if self.convert():
            self.create_cache()
        self.move_file()
        # self.sucess = True
        self.record.is_processed = True
        self.record.save()
=======
        try:
            if self.convert():
                self.create_cache()
        except Exception as err:
            logger.error(f"During convert and cache creation, {err}")
        finally:
            self.move_file()
            self.record.is_processed = True
            self.record.save()
>>>>>>> b8377cc (before modify app store structure)

    def convert(self):
>>>>>>> adding_process_node
        """Convert the uploaded file to mzml format with metadata.json, extract
        meta data
        return True if finished properly (geneated metadata.json file)
        """
<<<<<<< HEAD
        self.record.file_size = os.path.getsize(
            "media/" + self.record.temp_rawfile.name)/1024/1024/1024

        try:  # file converting
=======

        try:  # file converting, TODO change to msconvert for more file formats
            # https://proteowizard.sourceforge.io/download.html
            temp_file = os.path.join(
                settings.MEDIA_ROOT, self.record.temp_rawfile.name)
>>>>>>> adding_process_node
            result = subprocess.run(
                ['mono',
                 'file_manager/file_converters/ThermoRawFileParser'
                 '/ThermoRawFileParser.exe',
<<<<<<< HEAD
                 f'-i=media/{self.record.temp_rawfile.name}',
=======
                 f'-i={temp_file}',
>>>>>>> adding_process_node
                 '-m=0',
                 '-f=1',
                 '-L=1,2'],
                capture_output=True)
<<<<<<< HEAD
            time.sleep(1)
            meta_file = f'media/' \
                f'{os.path.splitext(self.record.temp_rawfile.name)[0]}' \
                '-metadata.json'

        except Exception as err:
            self.record.notes = "Raw file extraction failed, " + \
                type(err).__name__
            return False
        # extract meta data
=======

            time.sleep(1)

        except Exception as err:
            self.record.notes = type(err).__name__
        # extract meta data
        meta_file = f'media/' \
                    f'{os.path.splitext(self.record.temp_rawfile.name)[0]}' \
                    '-metadata.json'
>>>>>>> adding_process_node
        if os.path.exists(meta_file):
            f = open(meta_file,)
            data = json.load(f)
            f.close()
            os.remove(meta_file)
            self.record.acquisition_time = datetime.datetime.strptime(
                data["FileProperties"][2]["value"],
                "%m/%d/%Y %H:%M:%S")
            self.record.instrument_model = \
                data["InstrumentProperties"][0]["value"]
            self.record.instrument_sn = \
                data["InstrumentProperties"][2]["value"]
            to_tz = timezone.get_default_timezone()
            acquisition_time = self.record.acquisition_time.astimezone(
                to_tz)
            self.file_year, self.file_month, self.file_day = \
                acquisition_time.year, acquisition_time.month, \
                acquisition_time.day

<<<<<<< HEAD
            return True
=======
<<<<<<< HEAD
            return True
        else:
            if self.record.notes is None:
                self.record.notes = "Raw file extraction failed "
            if 'result' in locals():
                self.record_description = result
            to_tz = timezone.get_default_timezone()
            self.record.acquisition_time = self.record.uploaded_time
            # compromise, otherwise on acquisition time for sort
            upload_time = self.record.uploaded_time.astimezone(
                to_tz)
            self.file_year, self.file_month, self.file_day = \
                upload_time.year, upload_time.month, \
                upload_time.day
=======
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
                    output = docker.run(
                        converter_image,
                        converter_cmd,
                        volumes=[("/var/temp", "/data")],
                        interactive=True,
                        remove=True,
                    )
                else:  # not inside containner
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
        time.sleep(30)
        if os.path.exists(self.mzML):
            return True
        else:
            self.record.notes = "Raw file extraction failed "
            logger.error("No mzML file was found after conversion")
<<<<<<< HEAD

>>>>>>> b8377cc (before modify app store structure)
=======
>>>>>>> 357d529 (Feb Prototype)
            return False
>>>>>>> adding_process_node

    def create_cache(self):
        """_Create pkl cache file from mzMl_
        """
<<<<<<< HEAD
        mzml_filename = f'media/' \
            f'{os.path.splitext(self.record.temp_rawfile.name)[0]}' \
            '.mzML'

        with open(mzml_filename, "r") as xml_obj:
            # coverting the xml data to Python dictionary
            my_dict = xmltodict.parse(xml_obj.read())
        xml_obj.close()
        os.remove(mzml_filename)
        ms1_rt = []
        ms1_basemz = []
=======
        retry = 0
        is_converted = False
        # file conversion fails sometimes, a re-try upto 6 time was used
        while (retry < settings.FILE_CONVERT_RETRY and not is_converted):
            try:
                with open(self.mzML, "r") as xml_obj:
                    # coverting the xml data to Python dictionary
                    my_dict = xmltodict.parse(xml_obj.read())
            except Exception as error:
                logger.warning(f"Convertion failed {retry+1} time, "
                               f"will retry until failed 5 times, {error}")
                self.convert()
            else:
                is_converted = True
            finally:
                xml_obj.close()
                retry = retry + 1
                if retry >= settings.FILE_CONVERT_RETRY and not is_converted:
                    logger.error(
                        f"{self.fullname} Convertion "
                        f"abandoned after {retry} retries.")
                    return

        if not self.creator_setting.exists() or \
                not self.creator_setting.first().replace_raw_with_mzML:
            os.remove(self.mzML)
        ms1_rt = []
>>>>>>> adding_process_node
        ms1_basemzintensity = []
        ms1_ticintensity = []
        ms2_rt = []
        ms2_injectiontime = []

<<<<<<< HEAD
        for i in range(0, len(my_dict["mzML"]["run"][
                "spectrumList"]["spectrum"])):
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
=======
        instrument_info = my_dict["indexedmzML"]["mzML"][
            "referenceableParamGroupList"][
            "referenceableParamGroup"]["cvParam"]

        if isinstance(instrument_info, list):
            self.record.instrument_model = instrument_info[0]["@name"]
            self.record.instrument_sn = next(
                item for item in instrument_info if item[
                    "@name"] == "instrument serial number")["@value"]

        else:  # for Bruker
            self.record.instrument_model = instrument_info["@name"]
            self.record.instrument_sn = my_dict["indexedmzML"][
                "mzML"]["instrumentConfigurationList"][
                "instrumentConfiguration"]["cvParam"]["@value"]
        self.record.acquisition_time = datetime.datetime.strptime(
            my_dict["indexedmzML"]["mzML"][
                "run"]["@startTimeStamp"], "%Y-%m-%dT%H:%M:%SZ")

        self.file_year, self.file_month, self.file_day = \
            self.record.acquisition_time.year, \
            self.record.acquisition_time.month, \
            self.record.acquisition_time.day

        for item in my_dict["indexedmzML"]["mzML"]["run"][
                "spectrumList"]["spectrum"]:
            if next(item for item in item["cvParam"] if item[
                    "@name"] == "ms level")["@value"] == "1":

                if isinstance(item["scanList"]["scan"]["cvParam"], list):
                    ms1_rt.append(float(next(
                        item for item in item["scanList"]["scan"][
                            "cvParam"] if item[
                            "@name"] == "scan start time")["@value"]))
                else:
                    ms1_rt.append(
                        float(item["scanList"]["scan"]["cvParam"]["@value"]))

                if isinstance(item["cvParam"], list):
                    ms1_basemzintensity.append(float(next(
                        item for item in item["cvParam"] if item[
                            "@name"] == "base peak intensity")["@value"]))
                else:
                    ms1_basemzintensity.append(
                        float(item["cvParam"]["@value"]))

                if isinstance(item["cvParam"], list):
                    ms1_ticintensity.append(float(next(
                        item for item in item["cvParam"] if item[
                            "@name"] == "total ion current")["@value"]))
                else:
                    ms1_ticintensity.append(float(item["cvParam"]["@value"]))

            try:
                if next(item for item in item["cvParam"] if item[
                        "@name"] == "ms level")[
                        "@value"] == "2":
                    ion_injection_time = float(next(
                        item for item in item["scanList"][
                            "scan"]["cvParam"] if item[
                            "@name"] == "ion injection time")["@value"])
                    if ion_injection_time != 0:
                        ms2_rt.append(float(next(
                            item for item in item["scanList"]["scan"][
                                "cvParam"] if item[
                                "@name"] == "scan start time")["@value"]))
                        ms2_injectiontime.append(ion_injection_time)
            except TypeError:
                pass  # only thermo data with MS has this info
            except Exception as err:
                logger.error(f'Error message during read xml {err}')
        plot_data = {"MS1_RT": ms1_rt,
>>>>>>> adding_process_node
                     "MS1_Basemzintensity": ms1_basemzintensity,
                     "MS1_Ticintensity": ms1_ticintensity,
                     "MS2_RT": ms2_rt,
                     "MS2_Injectiontime": ms2_injectiontime}

<<<<<<< HEAD
        pkl_location = f"media/primary_storage/pkl/{self.file_year}/" \
                       f"{self.file_month}/{self.file_day}/"\
                       f"{self.filename}.pkl"

        file_dir = f"media/primary_storage/pkl/{self.file_year}/" \
                   f"{self.file_month}/{self.file_day}/"
        check_folder = os.path.isdir(file_dir)
        if not check_folder:
            os.makedirs(file_dir)
        with open(pkl_location, "wb") as handle:
=======
        pkl_location = f"primary_storage/pkl/{self.file_year}/" \
            f"{self.file_month}/{self.file_day}/"\
            f"{self.filename}.pkl"\

        file_dir = os.path.dirname(os.path.join(
            settings.MEDIA_ROOT, pkl_location))
        check_folder = os.path.isdir(
            os.path.join(settings.MEDIA_ROOT, file_dir))
        if not check_folder:
            os.makedirs(file_dir)
        with open(os.path.join(settings.MEDIA_ROOT,
                               pkl_location), "wb") as handle:
>>>>>>> adding_process_node
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
        """_Move the file to the right position_
        """
        if self.record.project_name != "":
            file_dir = f"primary_storage/rawfiles/{self.file_year}/"\
                f"{self.file_month}/{self.record.project_name}/"
        else:
            file_dir = f"primary_storage/rawfiles/{self.file_year}/"\
                f"{self.file_month}/{self.file_day}/"
        check_folder = os.path.isdir(os.path.join(
            settings.MEDIA_ROOT, file_dir))
        if not check_folder:
            os.makedirs(os.path.join(
                settings.MEDIA_ROOT, file_dir))
<<<<<<< HEAD
        newfile_name = f"{file_dir}/{self.fullname}"
        if os.path.exists(os.path.join(
                settings.MEDIA_ROOT, newfile_name)):
            random_str = "".join(random.choice(
                string.ascii_lowercase) for i in range(4))
            newfile_name = (f"{file_dir}/"
                            f"{self.fullname.split('.')[0]}"
                            f"_{random_str}.{self.extension}")

        shutil.move(
            (os.path.join(
                settings.MEDIA_ROOT, self.record.temp_rawfile.name)),
            os.path.join(
                settings.MEDIA_ROOT, newfile_name))
=======

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
>>>>>>> adding_process_node

        FileStorageform = {
            "file_location": newfile_name,
            "file_type": 1
        }
<<<<<<< HEAD
        saved_storage = self.filestorage.objects.create(**FileStorageform, )
=======
        saved_storage = self.filestorage.objects.create(
            **FileStorageform, )
>>>>>>> adding_process_node

        self.record.newest_raw = saved_storage
        self.record.file_storage_indeces.add(saved_storage)
        self.record.temp_rawfile = None
        self.sucess = True
<<<<<<< HEAD


if __name__ == "__main__":
    print("Hello, World!")
=======
>>>>>>> adding_process_node
