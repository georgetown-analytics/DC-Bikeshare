from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import time
import os
import matplotlib.pyplot as plt
import sys

TIMESTR = time.strftime("%Y%m%d_%H%M%S")


def open_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive


def push_to_drive(custom_title, location, drive, link):
    file1 = drive.CreateFile(
        {'title': custom_title, "parents": [{
            "kind": "drive#fileLink", "id": link
        }]})
    file1.SetContentFile(location)
    file1.Upload()


def all_in_one_save(title, path, drive, link):
    if not os.path.exists(path):
        os.makedirs(path)
    filepath = path + '_' + title + '_' + TIMESTR + '.png'
    plt.savefig(filepath)
    push_to_drive(title, filepath, drive, link)
