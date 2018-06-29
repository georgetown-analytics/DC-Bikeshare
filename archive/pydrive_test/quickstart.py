# https://googledrive.github.io/PyDrive/docs/build/html/quickstart.html

from pydrive.auth import GoogleAuth
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.
