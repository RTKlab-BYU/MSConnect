"""
Used to do hot updates of the web server.
"""
import os
import subprocess
import time


def update_system():
    subprocess.call(["git", "clone", "https://github.com/RTKlab-BYU/Proteomic-Data-Manager.git", "/home/git_download"])
    subprocess.call(["git", "-C", "/home/", "rev-parse", "--short", "HEAD", ">>", "/home/web/file_manager/git_version"])
    subprocess.call(["/venv/bin/python3", "/home/web/manage.py", "collectstatic","--noinput"], cwd="/app/")
    subprocess.call(["rsync", "-a", "-v", "/home/git_download/web/file_manager", "/app/"])
    subprocess.call(["rsync", "-a", "-v", "/home/git_download/web/data_manager", "/app/"])
    subprocess.call(["rsync", "-a", "-v", "/home/git_download/web/schedule_archive", "/app/"])
    # rm -rf /home/git_download
    subprocess.call(["rm", "-rf", "/home/git_download"])
    time.sleep(5)


