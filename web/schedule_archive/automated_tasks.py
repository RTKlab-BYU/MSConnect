from django.core import management
from django.db.models import Q
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.db.models.functions.datetime import TruncMonth
import time
import pickle
import errno
import os
from django.utils import timezone
import random
import string

import subprocess
import glob
import shutil
from django.contrib.auth import get_user_model
from django.conf import settings
from file_manager.models import FileStorage, SampleRecord, UserSettings,\
    SystemSettings, WorkerStatus, DataAnalysisQueue, AppAuthor, ProcessingApp,\
    VisualizationApp
from django.utils.timezone import utc
User = get_user_model()
startTime = time.time()


# Generated default system settings


# # for view recent request (get, not post)
# if SystemSettings.objects.first() is None:

try:
    current_backup_settings = \
        SystemSettings.objects.first().auto_backup_settings
    current_surge_settings = \
        SystemSettings.objects.first().auto_purge_settings
except AttributeError:
    form_data = {
        'facility_name': "My Default"
    }
    SystemSettings.objects.create(**form_data, )
    current_backup_settings = \
        SystemSettings.objects.first().auto_backup_settings
    current_surge_settings = \
        SystemSettings.objects.first().auto_purge_settings
task_list = ["database", "rawfile", "processed_file"]


def hourly_task():
    print(datetime.now(), "Hourly task started")
    generate_cache_files()
    backup_task("Hourly")
    backup_systemfile()

    # remove_unused_files(SsdStorage, 4)
    # keep_storage_below("/", 90)
    print("Hourly task finished")


def daily_task():
    """deleted ssd record that are older than 1 month and uploaded more than
    a week ago
    """
    print(datetime.now(), " Daily task started")

    backup_task("Daily")
    purge_task()
    print(" Daily task finished")
    backup_systemfile()


def weekly_task():
    print(datetime.now())
    backup_task("Weekly")


def monthly_task():
    print(datetime.now())
    backup_task("Monthly")


def backup_task(time_string):
    for key, value in current_backup_settings.items():
        if value == time_string:
            key_list = key.split("_")  # _storage_task
            storage_index = int(key_list[-2])
            task_type = int(key_list[-1])

            if storage_index == 0 and task_type == 0:
                print("backup database")
                management.call_command('dbbackup', '-z', "--clean")
                # database back to primary storage
            elif task_type == 0:
                # copy lastest database to corresponding folder respectively
                try:
                    current_datafile = glob.glob(
                        os.path.join(settings.MEDIA_ROOT,
                                     f"{settings.STORAGE_LIST[0]}"
                                     f"/database_backup/*.gz"
                                     ))[-1]
                    target_datafile = \
                        current_datafile.replace(
                            settings.STORAGE_LIST[0],
                            settings.STORAGE_LIST[storage_index],
                            1)
                    shutil.copy(current_datafile, target_datafile)
                except IOError as e:
                    # try creating parent directories
                    os.makedirs(os.path.dirname(target_datafile))
                    shutil.copy(current_datafile, target_datafile)
            elif task_type == 1:  # backup rawfile
                # not most efficient, step through all recrod check missing
                for record in SampleRecord.objects.all():
                    is_backup = False
                    for item in record.file_storage_indeces.all():
                        if int(item.file_type) == storage_index+1:
                            is_backup = True
                    if not is_backup:
                        storage_index = storage_index

                        # try:
                        current_raw = os.path.join(
                            settings.MEDIA_ROOT,
                            record.newest_raw.file_location.name)
                        file_path, file_name = \
                            os.path.split(
                                record.newest_raw.file_location.name)
                        to_tz = timezone.get_default_timezone()

                        acquisition_time = \
                            record.acquisition_time.astimezone(to_tz)
                        file_year, file_month, file_day = \
                            acquisition_time.year, acquisition_time.month,\
                            acquisition_time.day

                        new_name = \
                            f"{settings.STORAGE_LIST[storage_index]}/" \
                            f"rawfiles/{file_year}/{file_month}/{file_day}/" \
                            f"{file_name}"
                        file_extension = file_name.split(".")[-1]

                        new_name = new_name.replace(
                            "." + file_extension, ".7z")
                        if os.path.exists(os.path.join(
                                settings.MEDIA_ROOT, new_name)):
                            random_str = "".join(random.choice(
                                string.ascii_lowercase) for i in range(4))
                            new_name = new_name.replace(
                                ".7z", "_" + random_str+".7z")
                        subprocess.run(['7z', 'a',  os.path.join(
                            settings.MEDIA_ROOT, new_name), current_raw,
                            "-mx=9", "-mmt=2"])

                        if (os.path.exists(os.path.join(
                                settings.MEDIA_ROOT, new_name))):
                            FileStorageform = {
                                "file_location": new_name,
                                'file_type': storage_index+1
                            }
                            fileStorage_new = FileStorage.objects.create(
                                **FileStorageform, )
                            record.file_storage_indeces.add(
                                fileStorage_new)
                            print(
                                record.pk,
                                storage_index, task_type,
                                " backup finished")
                        else:
                            print(
                                record.pk,
                                storage_index, task_type,
                                " backup failed")

            elif task_type == 2:  # backup processed_file
                # not most efficient, step through all recrod check missing
                for record in DataAnalysisQueue.objects.all():
                    if record.finish_time is None:  # not finished running
                        continue
                    is_backup = False
                    for item in record.backup_indeces.all():
                        if int(item.file_type) == storage_index+6:
                            is_backup = True
                    if not is_backup:
                        # try:
                        file_list = ["input_file_1", "input_file_2",
                                     "input_file_3", "output_file_1",
                                     "output_file_2", "output_file_3", ]

                        url_list = []
                        to_tz = timezone.get_default_timezone()

                        finish_time = record.finish_time.astimezone(
                            to_tz)
                        file_year, file_month, file_day = finish_time.year, \
                            finish_time.month, finish_time.day
                        zip_name = \
                            f"{settings.STORAGE_LIST[storage_index]}/"
                        f"processqueue/{file_year}/{file_month}/"
                        f"{file_day}/{record.processing_name}.7z"
                        if os.path.exists(os.path.join(
                                settings.MEDIA_ROOT, zip_name)):
                            random_str = "".join(random.choice(
                                string.ascii_lowercase) for i in range(4))
                            zip_name = zip_name.replace(
                                ".7z", "_" + random_str+".7z")

                        for item_name in file_list:
                            current_url = getattr(record, item_name)
                            if current_url is not None and current_url != "":

                                add_file_name = \
                                    os.path.join(
                                        settings.MEDIA_ROOT, current_url.name)
                                subprocess.run(['7z', 'a',  os.path.join(
                                    settings.MEDIA_ROOT, zip_name),
                                    add_file_name,
                                    "-mx=9", "-mmt=2"])

                        if (os.path.exists(os.path.join(
                                settings.MEDIA_ROOT, zip_name))):
                            FileStorageform = {
                                "file_location": zip_name,
                                'file_type': storage_index+6
                            }
                            fileStorage_new = FileStorage.objects.create(
                                **FileStorageform, )
                            record.backup_indeces.add(
                                fileStorage_new)
                            print(
                                record.pk,
                                storage_index, task_type,
                                "process backup finished")
                        else:
                            print(
                                record.pk,
                                storage_index, task_type,
                                "process backup failed")


def purge_task():
    now = datetime.utcnow().replace(tzinfo=utc)

    for key, value in current_surge_settings.items():
        if value is None or value == "":
            continue
        key_list = key.split("_")  # _storage_task
        storage_index = int(key_list[-2])
        task_type = int(key_list[-1])
        if task_type == 0:  # purge old databse file
            try:
                pruge_direct = os.path.join(
                    settings.MEDIA_ROOT,
                    f"{settings.STORAGE_LIST[storage_index]}"
                    f"/database_backup/"
                )

                current_time = time.time()  # TODO change to datetime format
                for f in os.listdir(pruge_direct):
                    creation_time = os.path.getctime(f)
                    if (current_time - creation_time) // (24 * 3600) \
                            >= int(value):
                        os.remove(f)
                        print('{} removed'.format(f))

            except Exception as e:
                print(e)
        elif task_type == 1:  # purge old raw file
            for record in SampleRecord.objects.all():
                if (now - record.uploaded_time).days >= int(value):
                    print((now - record.uploaded_time).days)
                    for item in record.file_storage_indeces.all():
                        if int(item.file_type) == storage_index+1:
                            try:
                                os.remove(os.path.join(
                                    settings.MEDIA_ROOT, item.file_location))
                                item.file_location = None
                                item.save()
                            except Exception as error:
                                print(
                                    f"{error} remove {item.file_location}")

        elif task_type == 2:  # purge old process file
            for record in DataAnalysisQueue.objects.all():
                if (now - record.finish_time).days >= int(value):
                    print((now - record.finish_time).days)

                    for item in record.backup_indeces.all():
                        if int(item.file_type) == storage_index+1:
                            try:
                                os.remove(os.path.join(
                                    settings.MEDIA_ROOT, item.file_location))
                                item.file_location = None
                                item.save()
                            except Exception as error:
                                print(
                                    f"{error} remove {item.file_location}")


def backup_systemfile():
    print("backup system supporting files, e.g., process app etc")
    sys_file_backup = SystemSettings.objects.first().systemfile_backup_settings
    folder_to_back = os.path.join(
        settings.MEDIA_ROOT, f"{settings.STORAGE_LIST[0]}/systemfiles_backup")
    target_file = os.path.join(
        settings.MEDIA_ROOT,
        f"{sys_file_backup['system_file_backup_target']}/backups/backup.zip")
    subprocess.run(['7z', 'a',  target_file, folder_to_back,
                    "-mx=9", "-mmt=2"])


def generate_cache_files():
    cache_file = "file_manager/cache/dash_cache.pickle"

    data_daily = SampleRecord.objects.all().annotate(date=TruncDay(
        'acquisition_time')).values("date").annotate(
        created_count=Count('id')).order_by("-date")
    data_monthly = SampleRecord.objects.all().annotate(month=TruncMonth(
        'acquisition_time')).values("month").annotate(
        created_count=Count('id')).order_by("-month")
    by_user = SampleRecord.objects.all().values("record_creator_id").annotate(
        total=Count('record_creator_id')).order_by('-total')
    daily_data = []
    daily_lables = []
    monthly_data = []
    monthly_lables = []
    user_names = []
    user_counts = []
    for n in range(0, 30):
        try:
            if data_daily[29-n]["date"] is not None:
                daily_lables.append(
                    data_daily[29-n]["date"].strftime("%B-%d-%Y"))
                daily_data.append(data_daily[29-n]["created_count"])
        except IndexError:
            print(f"Less than {29-n} days of data")
    for n in range(0, 12):
        try:
            if data_monthly[11-n]["month"] is not None:
                monthly_lables.append(
                    data_monthly[11-n]["month"].strftime("%B-%Y"))
                monthly_data.append(data_monthly[11-n]["created_count"])
        except IndexError:
            print(f"Less than {11-n} month of data")
    for item in by_user[:10]:
        if item["record_creator_id"] is not None:
            user_names.append(User.objects.get(
                id=int(item["record_creator_id"])).username)
            user_counts.append(item["total"])

    total, used, free = shutil.disk_usage(
        os.path.join(settings.MEDIA_ROOT,
                     f"{settings.STORAGE_LIST[0]}/"))

    try:
        back_total, back_used, back_free = \
            shutil.disk_usage(os.path.join(settings.MEDIA_ROOT,
                                           f"{settings.STORAGE_LIST[1]}/"))
    except OSError:
        # prevent error while debug on other systems
        back_total, back_used, back_free = 1*(2**30), 1*(2**30), 1*(2**30)

    try:
        remote_total, remote_used, remote_free = shutil.disk_usage(
            os.path.join(settings.MEDIA_ROOT,
                         f"{settings.STORAGE_LIST[2]}/"))
    except OSError:
        # prevent error while debug on other systems
        remote_total, remote_used, remote_free = 1 * \
            (2**30), 1*(2**30), 1*(2**30)

    try:
        offline_total, offline_used, offline_free = shutil.disk_usage(
            os.path.join(settings.MEDIA_ROOT,
                         f"{settings.STORAGE_LIST[3]}/"))
    except OSError:
        # prevent error while debug on other systems
        offline_total, offline_used, offline_free = 1 * \
            (2**30), 1*(2**30), 1*(2**30)
    cached_data = {
        "records": SampleRecord.objects.count(),
        "users": User.objects.count(),
        "time": int((time.time() - startTime)/3600),
        "total": int(total // (2**30)),
        "used": int(used // (2**30)),
        "free": int(free // (2**30)),
        "percent": int(free/total*100),
        'labels': ["used", "free"],
        'data': [int(used // (2**30)), int(free // (2**30))],
        "back_total": int(back_total // (2**30)),
        "back_used": int(back_used // (2**30)),
        "back_free": int(back_free // (2**30)),
        "back_percent": int(back_free/back_total*100),
        'back_labels': ["used", "free"],
        'back_data': [int(back_used // (2**30)), int(back_free // (2**30))],
        'remote_labels': ["used", "free"],
        'remote_data': [int(remote_used // (2**30)),
                        int(remote_free // (2**30))],
        'offline_labels': ["used", "free"],
        'offline_data': [int(offline_used // (2**30)),
                         int(offline_free // (2**30))],
        'daily_data': daily_data,
        'daily_labels': daily_lables,
        'monthly_data': monthly_data,
        'monthly_labels': monthly_lables,
        'user_data': user_counts,
        'user_labels': user_names,
    }
    with open(cache_file, 'wb') as handle:
        pickle.dump(cached_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
