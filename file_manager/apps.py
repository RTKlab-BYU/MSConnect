from django.apps import AppConfig


class FileManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'file_manager'

    def ready(self):
        from schedule_archive import archive
        archive.start()
