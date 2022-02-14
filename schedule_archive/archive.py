from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from schedule_archive import automated_tasks

scheduler = BackgroundScheduler()


def start():
    scheduler.add_job(automated_tasks.hourly_task, 'cron', minute=5)
    # scheduler.add_job(automated_tasks.daily_task, 'cron', minute=37)
    scheduler.add_job(automated_tasks.daily_task, 'cron', hour=3)
    scheduler.add_job(automated_tasks.weekly_task, 'cron', day_of_week=6)
    scheduler.add_job(automated_tasks.monthly_task, 'cron', day=3)
    scheduler.start()
    import data_manager.notebook_setting

    if hasattr(data_manager.notebook_setting, 'notebook_mode'):
        if data_manager.notebook_setting.notebook_mode is True:
            scheduler.shutdown()
            print("Django system initized and scheduler shutdown")


def schedule_stop():
    scheduler.shutdown()
    print("Django system initized and scheduler shutdown")
