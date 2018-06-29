from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

drive = GoogleDrive(gauth)

# Create GoogleDriveFile instance with title 'Text2.txt'.
file1 = drive.CreateFile({'title': 'Test2.txt',
                          "parents": [{"kind": "drive#fileLink", "id": '1VYhVqDrEJJ8wos0AZQOtfnH20nXERfC4'}]})
file1.SetContentString('Success!')  # Set content of the file from given string.
file1.Upload()
