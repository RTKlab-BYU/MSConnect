from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from schedule_archive import automated_tasks
import pickle
import os
scheduler = BackgroundScheduler()
schedule_setting_file = "system_configure/schedule.pkl"
if os.path.isfile(schedule_setting_file):
    with open(schedule_setting_file, 'rb') as f:
        schedule_setting_dict = pickle.load(f)
else:
    schedule_setting_dict = {
        'schedule_hourly': '5',
        'schedule_daily': '3',
        'schedule_weekly': '6',
        'schedule_monthly': '3'
    }


def start():
    scheduler.add_job(automated_tasks.hourly_task, 'cron',
                      minute=int(schedule_setting_dict['schedule_hourly']))
    scheduler.add_job(automated_tasks.daily_task, 'cron',
                      hour=int(schedule_setting_dict['schedule_daily']))
    scheduler.add_job(automated_tasks.weekly_task, 'cron', day_of_week=int(
        schedule_setting_dict['schedule_weekly']))
    scheduler.add_job(automated_tasks.monthly_task, 'cron',
                      day=int(schedule_setting_dict['schedule_monthly']))
    scheduler.start()
    import data_manager.notebook_setting

    if hasattr(data_manager.notebook_setting, 'notebook_mode'):
        if data_manager.notebook_setting.notebook_mode is True:
            scheduler.shutdown()
            print("Django system initized and scheduler shutdown")


def schedule_stop():
    scheduler.shutdown()
    print("Django system initized and scheduler shutdown")