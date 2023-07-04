"""
Used to do hot updates of the web server.
"""
import subprocess
import time


def update_system(other_settings=None):
    """
    Updates the system by pulling the latest version of the code from github or system setting.
    """
    if ('repository' in other_settings and len(other_settings['repository']) != 0) and (
        'branch' in other_settings and len(other_settings['branch']) != 0):
        subprocess.call([
            "git", "clone","--single-branch", f"--branch {other_settings['branch']}",
            other_settings['repository'],"/home/git_download"])
    else:
        subprocess.call(["git", "clone", "https://github.com/RTKlab-BYU/Proteomic-Data-Manager.git", "/home/git_download"])
    f = open("/home/git_download/web/file_manager/git_version", "w")
    subprocess.call(["git", "-C", "/home/git_download", "rev-parse", "--short", "HEAD"], stdout=f)
    f.close()
    subprocess.call(["/venv/bin/python3", "/home/git_download/web/manage.py", "collectstatic","--noinput"], cwd="/app/")
    subprocess.call(["rsync", "-a", "-v", "/home/git_download/web/file_manager", "/app/"])
    subprocess.call(["rsync", "-a", "-v", "/home/git_download/web/data_manager", "/app/"])
    subprocess.call(["rsync", "-a", "-v", "/home/git_download/web/schedule_archive", "/app/"])
    #  rm -rf /home/git_download
    subprocess.call(["rm", "-rf", "/home/git_download"])
    time.sleep(3)
    