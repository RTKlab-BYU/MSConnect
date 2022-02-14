#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    print(sys.argv)
    import data_manager.notebook_setting
    data_manager.notebook_setting.init_notebook_mode()
    if "--notebook" in sys.argv:
        data_manager.notebook_setting.notebook_mode = True
        print("notebook mode")
    else:
        data_manager.notebook_setting.notebook_mode = False

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'data_manager.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
