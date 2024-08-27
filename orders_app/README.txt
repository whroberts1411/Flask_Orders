This FLASK website is implemented as a python package.
The top-level folder (Flask_Orders) contains only the python package
itself, nothing else.

The package name is "orders_app", and all of the site code is
found within this folder. The Flask site name is "app" and is 
created in the __init__.py module, which is executed when the
website is started; this is done from the run.bat file, but could 
also be done from the command line.

Note that for deployment, the run.bat file would NOT be used.