import os
import pickle

from apscheduler.schedulers.background import BackgroundScheduler

from django.conf import settings

from schedule_archive import automated_tasks
import data_manager.notebook_setting

import logging


scheduler = BackgroundScheduler()


logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.WARNING)


if os.path.isfile(settings.SCHEDULE_SETTING_FILE):
    with open(settings.SCHEDULE_SETTING_FILE, 'rb') as f:
        schedule_setting_dict = pickle.load(f)
else:
    schedule_setting_dict = settings.DEFAULT_SCHEDULE


def start():
    """_Start the scheudler and add jobs_
    """
    scheduler.add_job(automated_tasks.hourly_task, 'cron',
                      minute=int(schedule_setting_dict['schedule_hourly']))
    scheduler.add_job(automated_tasks.daily_task, 'cron',
                      hour=int(schedule_setting_dict['schedule_daily']))
    scheduler.add_job(automated_tasks.weekly_task, 'cron', day_of_week=int(
        schedule_setting_dict['schedule_weekly']))
    scheduler.add_job(automated_tasks.monthly_task, 'cron',
                      day=int(schedule_setting_dict['schedule_monthly']))
    scheduler.start()

    if hasattr(data_manager.notebook_setting, 'notebook_mode'):
        if data_manager.notebook_setting.notebook_mode is True:
            scheduler.shutdown()
            print("Django system initized and scheduler shutdown")


def schedule_stop():
    """_Stop the scheduler, especially useful if import the app in Jupiter
    Notebook_
    """
    scheduler.shutdown()
    print("Django system initized and scheduler shutdown")
