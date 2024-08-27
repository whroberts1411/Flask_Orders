"""
 Name:          config.py

 Purpose:       Configuration settings for Flask and its extensions.

 Author:        Bill

 Created:       26/07/2024

"""
#-------------------------------------------------------------------------------

import os

#-------------------------------------------------------------------------------

class Config():
    """ Flask config options will be stored as class variables. """

    # If not present as an environment variable, the default will be used.
    SECRET_KEY = os.environ.get('SECRET_KEY') or '23d4ni89234rnvh8737nzd78bw'
    # Folders on the server for uploads, etc.
    UPLOAD_DIR = 'uploads/'
    IMAGE_DIR = 'static/media/'
    PHOTO_DIR = 'static/images/'
    MUSIC_DIR = 'static/music/'
    VIDEO_DIR = 'static/video/'
    # API details for the Weather API site
    API_KEY = 'my api key'
    API_URL1 = 'https://api.weatherapi.com/v1/current.json'
    API_URL2 = 'https://api.weatherapi.com/v1/astronomy.json'
    # API details for YouTube videos
    YT_KEY = 'my api key'
    YT_API_URL = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={id}&key={apiKey}'
    YT_VID_URL = 'https://www.youtube.com/embed/'
    # Other stuff
    PAGE_SIZE = 15
    DATABASE = 'FlaskWebsite.db'


#-------------------------------------------------------------------------------
