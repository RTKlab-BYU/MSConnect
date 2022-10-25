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


class FileConverter():
    """convert the passed SampleRecord istance and covernt the file, extract
    data
    """

    def __init__(self, instance=None, FileStorage=None):
        self.record = instance
        self.sucess = False
        self.filestorage = FileStorage

        self.filename = os.path.splitext(instance.temp_rawfile.name)[
            0].split('/')[-1]
        self.extension = os.path.splitext(self.record.temp_rawfile.name)[1][1:]
        self.fullname = self.filename + "." + self.extension
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
        """Convert the uploaded file to mzml format with metadata.json, extract
        meta data
        return True if finished properly (geneated metadata.json file)
        """
        self.record.file_size = os.path.getsize(
            "media/" + self.record.temp_rawfile.name)/1024/1024/1024

        try:  # file converting
            result = subprocess.run(
                ['mono',
                 'file_manager/file_converters/ThermoRawFileParser'
                 '/ThermoRawFileParser.exe',
                 f'-i=media/{self.record.temp_rawfile.name}',
                 '-m=0',
                 '-f=1',
                 '-L=1,2'],
                capture_output=True)
            time.sleep(1)
            meta_file = f'media/' \
                f'{os.path.splitext(self.record.temp_rawfile.name)[0]}' \
                '-metadata.json'

        except Exception as err:
            self.record.notes = "Raw file extraction failed, " + \
                type(err).__name__
            return False
        # extract meta data
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

            return True

    def create_cache(self):
        """_Create pkl cache file from mzMl_
        """
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
        ms1_basemzintensity = []
        ms1_ticintensity = []
        ms2_rt = []
        ms2_injectiontime = []

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
                     "MS1_Basemzintensity": ms1_basemzintensity,
                     "MS1_Ticintensity": ms1_ticintensity,
                     "MS2_RT": ms2_rt,
                     "MS2_Injectiontime": ms2_injectiontime}

        pkl_location = f"media/primary_storage/pkl/{self.file_year}/" \
                       f"{self.file_month}/{self.file_day}/"\
                       f"{self.filename}.pkl"

        file_dir = f"media/primary_storage/pkl/{self.file_year}/" \
                   f"{self.file_month}/{self.file_day}/"
        check_folder = os.path.isdir(file_dir)
        if not check_folder:
            os.makedirs(file_dir)
        with open(pkl_location, "wb") as handle:
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

        FileStorageform = {
            "file_location": newfile_name,
            "file_type": 1
        }
        saved_storage = self.filestorage.objects.create(**FileStorageform, )

        self.record.newest_raw = saved_storage
        self.record.file_storage_indeces.add(saved_storage)
        self.record.temp_rawfile = None
        self.sucess = True


if __name__ == "__main__":
    print("Hello, World!")
