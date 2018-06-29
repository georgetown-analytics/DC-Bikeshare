from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

drive = GoogleDrive(gauth)

# Auto-iterate through all files that matches this query

''' 1VYhVqDrEJJ8wos0AZQOtfnH20nXERfC4 is the folder ID for CaBi Data
    The only way to navigate the folder structure in by calling the folder ID per:
    https://stackoverflow.com/questions/40224559/list-of-file-in-a-folder-drive-api-pydrive
    We'll need to have a dictionary of folder IDs saved in a class so that we want to leverage so we can make this
    code more explicit
'''
file_list = drive.ListFile({'q': "'1VYhVqDrEJJ8wos0AZQOtfnH20nXERfC4' in parents and trashed=false"}).GetList()
for file1 in file_list:
    print('title: %s, id: %s' % (file1['title'], file1['id']))
