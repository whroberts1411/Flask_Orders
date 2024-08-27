"""
 Name:          __init__.py

 Purpose:       Startup for flask application. First time using Flask for web
                development, so this website is mainly just a
                demo of the sort of things that I would want to do with a
                "proper" website. User authentication, database access,
                sending emails, connecting to external api sites, etc.

 Author:        Bill

 Created:       25/07/2024

"""
#-------------------------------------------------------------------------------

from flask import Flask
from orders_app.config import Config

app = Flask(__name__)

# Store the configuration options
app.config.from_object(Config)

from orders_app import routes

#-------------------------------------------------------------------------------

