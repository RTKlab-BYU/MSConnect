from django.core import management
from django.db.models import Q
from datetime import datetime, timedelta
from file_manager.models import RawFile, SpectromineQueue, SpectromineWorker, \
    NoteFile, SsdStorage, HdStorage, RemoteStorage, OfflineStorage
import os
import shutil
from django.conf import settings


def hourly_task():
    print(datetime.now(), "Hourly task started")
    management.call_command('dbbackup', '-z', "--clean")  # django-dbbackup
    remove_unused_files(SsdStorage, 4)
    keep_storage_below("/", 90)
    print("Hourly task finished")


def daily_task():
    """deleted ssd record that are older than 1 month and uploaded more than
    a week ago
    """
    print(datetime.now(), " Daily task started")
    time_threshold = datetime.now() - timedelta(days=14)
    up_time_threshold = datetime.now() - timedelta(days=3)
    old_record = RawFile.objects.filter(
        Q(acquisition_time__lt=time_threshold)
        & Q(uploaded_at__lt=up_time_threshold) & Q(ssd_storage__isnull=False))
    for item in old_record:
        print(f"move {item} from ssd to hd")
        RawFile.objects.filter(pk=item.pk).update(ssd_storage=None)
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(HdStorage)
        RawFile.objects.filter(pk=item.pk).update(
            content_type=ct, object_id=item.hd_storage.pk)
        RawFile.objects.filter(pk=item.pk).update(
            rawfile=item.hd_storage.filelocation)
    # remove unsued HD file (keep last 100)
    remove_unused_files(HdStorage, 100)
    remote_achieve()  # create remote achieve
    print(" Daily task finished")


def weekly_task():
    # delete unused HD files
    print(datetime.now())
    not_used_hd = HdStorage.objects.filter(rawfile=None).order_by('-pk')[50:]
    for item in not_used_hd:
        print(item)


def monthly_task():
    print(datetime.now())

    pass


def remove_unused_files(storage_obj, number_keep):
    print(f"start cleanning unused files {storage_obj}")
    print(storage_obj.objects.filter(
        rawfile=None).order_by('-pk'))
    not_used_storage = storage_obj.objects.filter(
        rawfile=None).order_by('-pk')[number_keep:]
    print(not_used_storage)
    if (len(not_used_storage) > 0):
        print(f"There are {len(not_used_storage)} to be deleted")
    for item in not_used_storage:
        print(item.filelocation)
        # try:
        try:
            os.remove(os.path.join("media/", item.filelocation.name))
            if (not os.path.exists(item.filelocation.name)):
                print(f"file {item.filelocation.name} deleted")
                storage_obj.objects.filter(pk=item.pk).delete()
        except OSError:
            print(f"file {item.filelocation.name} deleting failed")

            #     if (not os.path.exists(item.filelocation.name)):
        #         storage_obj.objects.filter(pk=item.pk).delete()


def keep_storage_below(directory, threshold_percentage=80):
    """Used as emergence clean up when daily clean up can't keep up

    Args:
        directory ([type]): [description]
        threshold_percentage (int, optional): [description]. Defaults to 80.
    """
    total, used, free = shutil.disk_usage(directory)
    print(f"current usage is {int(used/total*100)}% ")
    # TODO: finish auto clean up if pass threshold


def remote_achieve():
    no_backup_entry = RawFile.objects.filter(remote_storage__isnull=True)
    for item in no_backup_entry:
        try:
            relative_name = RawFile.objects.filter(
                pk=item.pk)[0].hd_storage.filelocation.name
            current_raw = os.path.join(settings.MEDIA_ROOT, relative_name)
            new_name = relative_name.replace(
                "hdstorage", "remote_archive", 1)
            new_name = new_name.replace(
                ".raw", ".7z", 1)
            import subprocess
            subprocess.run(['7z', 'a',  os.path.join(
                settings.MEDIA_ROOT, new_name), current_raw,
                "-mx=9", "-mmt=2"])
            pklform = {
                "filelocation": new_name,
            }
            remote_obj = RemoteStorage.objects.create(**pklform, )
            RawFile.objects.filter(pk=item.pk).update(
                remote_storage=remote_obj)
            print(item.pk, " worked")
        except OSError:
            print(item.pk, " failed")


# except IndexError:
#     print(n, "doesn't exist")
