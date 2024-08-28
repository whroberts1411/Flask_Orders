"""
 Name:          routes.py

 Purpose:       Routing module for Flask. Each function handles the routing
                for a different website page. The site doesn't use the Flask
                ORM for database access; it uses the SQLite database module
                that is used for all my other programs (makes query design
                much easier).

 Author:        Bill

 Created:       25/07/2024

 Amended:       15/08/2024
                Added the new module datastore.py, containing a single class
                DataStore. This holds large amounts of data between session
                to prevent the session variable running out of space (4k limit).
                Each screen has its own separate data store in this class.

                22/08/2024
                Change module datastore.py to use a single dictionary for
                storage. This will then be used the same as the session object,
                substituting "session" by "ds.store".

"""
#-------------------------------------------------------------------------------

from flask import render_template, flash, redirect, url_for, session, request
from orders_app import app

from orders_app.forms import (LoginForm, RegisterForm, getEmailForm,
                              DateRangeForm, ImageBrowseForm, getImageEditForm,
                              MusicBrowseForm, VideoLoadForm )
from werkzeug.utils import secure_filename
import requests
import json

import orders_app.dbAccess as db
import orders_app.emailClass as ec
email = ec.EmailClass()

import orders_app.datastore as datastore
ds = datastore.DataStore()
from datetime import datetime
import time

import matplotlib.pyplot as plt
# This configures matplotlib as non-interactive - can only write to files.
# Prevents the warning message about thread failure.
import matplotlib
matplotlib.use('agg')

import os
import shutil
from functools import wraps

# Values that are used on most screens - just calculate them once.
currdate = datetime.now().strftime("%A, %d/%m/%Y")
year = datetime.now().strftime("%Y")

#-------------------------------------------------------------------------------
# Decorator function (closure) to check that the user is logged in.
#-------------------------------------------------------------------------------

def login_required(route):
    @wraps(route)
    def inner(*args, **kwargs):
        if not session.get('username', None):
            return redirect(url_for('login'))
        return route(*args, **kwargs)
    return inner

#-------------------------------------------------------------------------------
# Create a matplotlib pie chart.
#-------------------------------------------------------------------------------

def getPlot(data):
    """ Create a pie chart from the supplied data. Nice and simple. """

    cat, tot = [], []

    for item in data:
        cat.append(item[0])
        tot.append(int(item[1]))

    plt.close()
    fig = plt.Figure(figsize=(1,1))
    plt.pie(tot, labels=cat)

    return plt

#-------------------------------------------------------------------------------
# Create a matplotlib pie chart (again).
#-------------------------------------------------------------------------------

def getPlot2(data):
    """ The 'data' set has the description in data[1] and total cost in
        data[3]. """

    desc, tot = [], []

    for idx, item in enumerate(data):
        desc.append(item[1])
        tot.append(item[3])

    plt.close()
    fig = plt.Figure(figsize=(1,1))
    plt.pie(tot, labels=desc)

    return plt

#-------------------------------------------------------------------------------
# This is the route to the main home page for the site.
#-------------------------------------------------------------------------------

@app.route('/')
@app.route('/index')
@login_required
def index():

    res = db.getCat()
    res1 = db.getCatCounts()
    plot = getPlot(res1)
    plot.savefig(os.path.join('static', 'media', 'plot.png'),
                                bbox_inches='tight')

    res3 = db.getItemCosts()
    plot2 = getPlot2(res3)
    plot2.savefig(os.path.join('static', 'media', 'plot2.png'),
                                bbox_inches='tight')

    return render_template('index.html', title='Home',
                           user=session.get('username', None), categories=res,
                           postdate=currdate, year=year, cat=res1,
                           items=res3, )

#-------------------------------------------------------------------------------
# Route for the 'Orders' navbar option. Use pagination to display screens of
# 15 records at a time.
#-------------------------------------------------------------------------------

@app.route('/orders/<page>', methods=['GET', 'POST'])
@login_required
def orders(page):

    rows = app.config['PAGE_SIZE']

    if not ds.store.get('dict', {}):
        ds.store['dict'] = {'page':page, 'count':rows, 'size':0}

    # Store the page request in the session dict
    ds.store['dict']['page'] = page

    # Calculate the end index for the list slicing
    if page == 'f': ds.store['dict']['count'] = rows
    elif page == 'n': ds.store['dict']['count'] += rows
    elif page == 'p': ds.store['dict']['count'] -= rows
    elif page == 'l': ds.store['dict']['count'] = ds.store['dict']['size']

    # Check for, and correct, out-of-range values
    if ds.store['dict']['count'] < rows :
        ds.store['dict']['count'] = rows
    if (ds.store['dict']['count'] > ds.store['dict']['size'] and
        ds.store['dict']['size'] != 0):
        ds.store['dict']['count'] = ds.store['dict']['size']

    form =DateRangeForm()
    if form.validate_on_submit():
        sdate = form.startDate.data.strftime('%Y-%m-%d')
        edate = form.endDate.data.strftime('%Y-%m-%d')
        res = db.getOrders(sdate, edate)
        # Store the data, and number of records, returned
        ds.store['orderdata'] = res
        ds.store['dict']['size'] = len(res)

    # Do this whichever button was clicked (main or pagination)
    count = ds.store['dict']['count']
    ds.store['orders'] = ds.store.get('orderdata',[])[count-rows:count]

    return render_template('orders.html', title='Orders', currdate=currdate,
                            orders=ds.store.get('orders',[]), year=year,
                            form=form, page=ds.store['dict']['page'])

#-------------------------------------------------------------------------------
# Route to page for testing Weather API call
#-------------------------------------------------------------------------------

@app.route('/weather', methods=['GET', 'POST'])
@login_required
def weather(orig=''):

    # Initialise the storage tables that we will use for the API results
    loc, air, astro, res = [], [], [], []
    clearScreen = False     # is the lower part of the screen to be displayed?

    # Get and store the locations from the database
    if not ds.store.get('locations', None):
        locations = [''] + db.getLocations()
        ds.store['locations'] = locations
    else:
        locations = ds.store['locations']

    # Make the call to the Weather API site
    if request.method == 'POST':
        if request.form.get('action') == 'location':
            data = request.form['locations']
            ds.store['data'] = data
            if data:
                clearScreen = False
                return redirect(url_for('api'))
            else:
                clearScreen = True

    # Split the returned dictionary into 4 formatted lists
    if ds.store.get('data',''):
        loc, air, astro, res = db.reformat(ds.store['data'])
        ds.store['all'] = [loc, air, astro, res]
    else:
        clearScreen = True

    return render_template('weather.html', title='Weather',
                           user=session['username'], year=year,
                           locations=locations, data=ds.store.get('all'),
                           clearScreen=clearScreen)

#-------------------------------------------------------------------------------
# Route for Weather API call. No template for this one.
#-------------------------------------------------------------------------------

@app.route('/api', methods=['GET', 'POST'])
def api():

    # Get the details required for the API call
    ret = db.getLatLon(ds.store.get('data',[]))[0]
    lat = ret[0]
    lon = ret[1]
    key = app.config["API_KEY"]
    url1 = app.config["API_URL1"]   # current weather conditions
    url2 = app.config['API_URL2']   # astronomy data (sun, moon)

    # Assemble the complete API request url
    apiReq1 = url1 + '?key=' + key + '&q=' + lat + ',' + lon + '&aqi=yes'
    apiReq2 = url2 + '?key=' + key + '&q=' + lat + ',' + lon

    # Call the Weather API site
    try:
        response = requests.get(apiReq1)
        response.raise_for_status()
        data1 = response.json()
        response = requests.get(apiReq2)
        response.raise_for_status()
        data2 = response.json()
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), 500
    except Exception as err:
        return jsonify({'error': f'Other error occurred: {err}'}), 500

    # Concatenate the returned data and store in session
    ds.store['data'] = dict(data2, **data1)

    return redirect(url_for('weather', orig='api'))

#-------------------------------------------------------------------------------
# Route for the 'Send Email' navbar option.
#-------------------------------------------------------------------------------

@app.route('/email', methods=['GET', 'POST'])
@login_required
def email():

    uploadTo = app.config["UPLOAD_DIR"]

    # There may be one or more recipients, which should be passed as a list.
    # Any attachments will also be passed as a list - note that this is an
    # optional field, and so must be cleared before each call.

    form = getEmailForm(session['email'])()
    if form.validate_on_submit():
        recipList = [] + form.recipient.data.split(',')
        email.sentFrom = form.sender.data
        email.to = recipList
        email.subject = form.subject.data
        email.body = form.body.data

        email.attachment = []
        if form.attachment.data:
            attach = []
            for file in form.attachment.data:
                file_filename = secure_filename(file.filename)
                file.save(uploadTo + file_filename)
                attach.append(uploadTo + file_filename)
            email.attachment = attach

        msg = email.sendMail()

        flash(msg)
        return redirect(url_for('index'))

    return render_template('email.html', title='Send Email', form=form,
                           user=session.get('username'), year=year)

#-------------------------------------------------------------------------------
# Route for the database schema page.
#   name : the name of the selected database table
#   option : either 'table', 'view' or 'rows'. If 'table' a list of columns
#            will be returned. If 'rows' the first 15 data records will be
#            returned.
#   If both as set to 'none', no selection has been made.
#-------------------------------------------------------------------------------

@app.route('/browsedb/<name>/<option>', methods=['GET', 'POST'])
@login_required
def browsedb(name, option):

    dbase = app.config['DATABASE']

    if request.method == 'POST':
        rad = request.form.get("radSchema")
        if not rad: rad = 'tables'

        if rad == 'tables':
            res = db.getTables()
        else:
            res = db.getViews()

        ds.store['schema'] = res
        ds.store['radio'] = rad
        ds.store['rowdata'] = []
        ds.store['viewdef'] = ''

    if name != 'none':
        res, viewDef = db.getTableDets(name, option)
        ds.store['rowdata'] = res
        ds.store['viewdef'] = viewDef

    return render_template('browsedb.html', title='Database Schema', year=year,
                            database=dbase, schema=ds.store.get('schema', []),
                            rad=ds.store.get('radio', ''),
                            table=ds.store.get('rowdata',[]),
                            view=ds.store.get('viewdef',''))

#-------------------------------------------------------------------------------
# Route for the image browser page.
#-------------------------------------------------------------------------------

@app.route('/browseimages', methods=['GET', 'POST'])
@login_required
def browseimages():

    folder = app.config['PHOTO_DIR']
    if not ds.store.get('thumbs', None):
        thumbs = db.getImageDetails()
        ds.store['thumbs'] = thumbs

    images = []
    form = ImageBrowseForm()
    if form.validate_on_submit():
        if form.newImages.data:
            for file in form.newImages.data:
                file_filename = secure_filename(file.filename)
                file.save(folder + file_filename)
                images.append(folder + file_filename)
            ret = db.storeNewImages(images, '640')
            thumbs = db.getImageDetails()
            ds.store['thumbs'] = thumbs

    return render_template('browseimages.html', title='Image Browser',
                            year=year, form=form,
                            thumbs=ds.store.get('thumbs', []),
                            total = len(ds.store.get('thumbs', [])))

#-------------------------------------------------------------------------------
# Route for image edit.
#-------------------------------------------------------------------------------

@app.route('/editimage/url=<path:image>', methods=['GET', 'POST'])
@login_required
def editimage(image):

    print(f'image : {image}')
    imgName = image.replace('_thumb','')    # original name (with 'thumb')
    fname = os.path.basename(imgName)       # original name, 'thumb' removed
    dirName = os.path.dirname(image) + '\\' # path, with trailing '\'
    tmp = os.path.splitext(fname)
    rootName = tmp[0]                       # orig. filename, no extension
    rootExt = tmp[1]                        # filename extension (leading '.')

    ret = db.getImageByName(imgName)
    ds.store['ImageEdit'] = ret[0]
    form = getImageEditForm(rootName, ret[0][1])()

    if form.validate_on_submit():
        newName = form.name.data
        newDesc = form.desc.data
        newName = dirName + newName + rootExt

        if (newName == ds.store['ImageEdit'][0] and
                newDesc == ds.store['ImageEdit'][1]) :
            msg = 'No changes detected - details not updated'
        else:
            db.updateImage(imgName, newName, newDesc)
            if image != newName:
                os.rename(imgName, newName)
                thumb = newName.replace('.', '_thumb.')
                os.rename(image, thumb)

            thumbs = db.getImageDetails()
            ds.store['thumbs'] = thumbs
            msg = 'Requested changes have been applied'

        flash(msg)
        return redirect(url_for('browseimages'))

    return render_template('editimage.html', title='Edit Image',
                            year=year, image=image.replace('_thumb',''),
                            thumb=image, form=form,
                            date=ret[0][2])

#-------------------------------------------------------------------------------
# Route for image delete.
#-------------------------------------------------------------------------------

@app.route('/deleteimage/url=<path:image>', methods=['GET', 'POST'])
@login_required
def deleteimage(image):

    if request.method == 'POST':
        if request.form.get('action') == 'yes':

            if os.path.isfile(image.replace("_thumb","")):
                os.remove(image.replace("_thumb",""))

            if os.path.isfile(image):
                os.remove(image)

            db.deleteImage(image)
            thumbs = db.getImageDetails()
            ds.store['thumbs'] = thumbs

            msg = f'Image {image.replace("_thumb","")} was deleted'

        if request.form.get('action') == 'no':
            msg = 'The image was not deleted'

        flash(msg)
        return redirect(url_for('browseimages'))

    return render_template('deleteimage.html', title='Delete Image',
                            year=year,  image=image.replace('_thumb',''),
                            thumb=image)

#-------------------------------------------------------------------------------
# Route for changing the background image.
#-------------------------------------------------------------------------------

@app.route('/setbackground/url=<path:image>', methods=['GET', 'POST'])
@login_required
def setbackground(image):

    if request.method == 'POST':
        if request.form.get('action') == 'yes':

            if os.path.isfile(os.path.join('static', 'background.jpg')):
                os.remove(os.path.join('static', 'background.jpg'))

            if os.path.isfile(image):
                dest = shutil.copyfile(image,
                                       os.path.join('static', 'background.jpg'))

            msg = f'Background was changed to {image.replace("_thumb","")}'
            flash(msg)
            msg = f'Please close and reload this tab to see new background'
            flash(msg)

            return redirect(url_for('browseimages'))

        if request.form.get('action') == 'no':
            msg = 'Background was not changed'
            flash(msg)
            return redirect(url_for('browseimages'))

    return render_template('setbackground.html', title='Set Background Image',
                            year=year, image=image.replace('_thumb',''),
                            thumb=image)

#-------------------------------------------------------------------------------
# Route for the music player page.
#-------------------------------------------------------------------------------

@app.route('/music/url=<path:track>&delete=<delete>&page=<page>',
            methods= ['GET', 'POST'])
@login_required
def music(track, delete, page):

    rows = 10
    if not ds.store.get('dictMusic', {}):
        ds.store['dictMusic'] = {'page':page, 'count':rows, 'size':0}

    ds.store['dictMusic']['page'] = page

    # Calculate the end index for the list slicing
    if page == 'f': ds.store['dictMusic']['count'] = rows
    elif page == 'n': ds.store['dictMusic']['count'] += rows
    elif page == 'p': ds.store['dictMusic']['count'] -= rows
    elif page == 'l':  ds.store['dictMusic']['count'] = ds.store['dictMusic']['size']

    # Check for, and correct, out-of-range values
    if ds.store['dictMusic']['count'] < rows :
        ds.store['dictMusic']['count'] = rows
    if (ds.store['dictMusic']['count'] > ds.store['dictMusic']['size'] and
        ds.store['dictMusic']['size'] != 0):
        ds.store['dictMusic']['count'] = ds.store['dictMusic']['size']

    folder = app.config['MUSIC_DIR']
    if not ds.store.get('musicdata', []):
        ds.store['musicdata'] = db.getAudio()
        ds.store['dictMusic']['size'] = len(ds.store['musicdata'])

    if delete == 'yes':
        ret = db.deleteAudio(track)
        if os.path.isfile(track):
            os.remove(track)
        play = 'none'
        ds.store['musicdata'] = db.getAudio()
        ds.store['dictMusic']['size'] = len(ds.store['musicdata'])
    else:
        play = track

    tracks=[]
    form = MusicBrowseForm()
    if form.validate_on_submit():
        if form.newTracks.data:
            for file in form.newTracks.data:
                file_filename = secure_filename(file.filename)
                file.save(folder + file_filename)
                tracks.append(folder + file_filename)
            ret = db.storeAudio(tracks)
            ret = db.getAudio()
            ds.store['musicdata'] = ret
            ds.store['dictMusic']['size'] = len(ds.store['musicdata'])

    nameOnly = os.path.basename(track).replace('_', ' ').replace('.mp3', '')

    count = ds.store['dictMusic']['count']
    ds.store['pageTracks'] = ds.store['musicdata'][count-rows:count]

    return render_template('music.html', title='Music Player', form=form,
                           tracks=ds.store.get('pageTracks',[]),
                           play=play, trackname=nameOnly,
                           page=page, year=year)

#-------------------------------------------------------------------------------
# Route for the video player page.
#-------------------------------------------------------------------------------

@app.route('/video/url=<path:vid_url>&delete=<delete>', methods=['GET', 'POST'])
@login_required
def video(vid_url, delete):

    form = VideoLoadForm()
    if form.validate_on_submit():
        if request.form.get('action') == 'yt':
            ytid = form.ytident.data
            return redirect(url_for('youtube', ident=ytid))

        if request.form.get('action') == 'mp4':
            folder = app.config['VIDEO_DIR']
            mp4 = form.title.data
            file = form.newVideo.data
            file_filename = secure_filename(file.filename)
            file.save(folder + file_filename)
            ret = db.storeVideo(mp4, folder+file_filename, 'mp4')
            msg = 'Video (mp4) details stored on database successfully!'
            flash(msg)
            return redirect(url_for('video',vid_url='none',delete='no'))

        vid_play = 'none'

    if delete == 'yes':
        try:
            if vid_url.startswith('static'):
                if os.path.isfile(vid_url):
                    os.remove(vid_url)
        except Exception as ex:
            msg = 'Video was Playing and Locked - Please Try Again!'
            flash(msg)
            return redirect(url_for('video',vid_url='none',delete='no'))

        ret = db.deleteVideo(vid_url)
        vid_play = 'none'
        opt = ''
        return redirect(url_for('video',vid_url='none',delete='no'))
    else:
        vid_play = vid_url
        if vid_url.startswith('static'): opt = 'mp4'
        else: opt = 'yt'

    ret = db.getVideo()
    ds.store['videoData'] = ret

    return render_template('video.html', title='Video Player', form=form,
                            videos=ds.store['videoData'], vid_play=vid_play,
                            opt=opt, year=year)

#-------------------------------------------------------------------------------
# Call the YouTube API to get details of the selected video.
#-------------------------------------------------------------------------------

@app.route('/youtube/<ident>', methods=['GET', 'POST'])
def youtube(ident):

    # Get the required details for the call
    key = app.config['YT_KEY']
    url = app.config['YT_API_URL']
    vid_url = app.config['YT_VID_URL']
    # Add api key and video id to the two urls
    url = url.replace('{id}', ident)
    url = url.replace('{apiKey}', key)
    vid_url += ident

    # Get the data from the Google YouTube API...
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), 500

    # store the returned data
    res = db.storeVideo(data, vid_url, 'yt')
    msg = ' YouTube video details stored on database successfully!'
    flash(msg)

    return redirect(url_for('video',vid_url='none',delete='no'))

#-------------------------------------------------------------------------------
# Route to the user login page.
#-------------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        # Check the username and password on the database
        msg = db.getUser(form.username.data, form.password.data)
        if msg[0].startswith('Error'):
            flash(msg)
            return redirect(url_for('login'))
        else:
            session['email'] = msg[0]
            session['admin'] = msg[1]

        # User details are ok, so go to the home page
        session['username'] = form.username.data
        msg = f'User {form.username.data} is logged in '
        flash(msg)
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form, year=year)

#-------------------------------------------------------------------------------
# Route to the user logout page. No template for this one.
#-------------------------------------------------------------------------------

@app.route('/logout')
def logout():

    tmp = session.pop('username', None)
    flash(f'User {tmp} is signed out')

    # Now, clear down all session keys for this user, except for Flash
    # messages (these will begin with an underscore).
    x = [session.pop(key) for key in list(session.keys())
                            if not key.startswith('_')]

    # Clear the data stored in the DataStore class
    ds.clearStore()

    return redirect(url_for('login'))

#-------------------------------------------------------------------------------
# Site administration screen. Reset system variables, server-side storage and
# allow user admin flag setting.
#-------------------------------------------------------------------------------

@app.route('/admin/<delete>/<user>', methods=['GET', 'POST'])
def admin(delete, user):

    sessVar = []
    for key in list(session.keys()):
        if key != 'csrf_token':
            sessVar.append(key)

    # Clear session variables except username, email, admin and flash messages
    for key in list(session.keys()):
        if key in ('username', 'email', 'admin'): continue
        if key.startswith('_'): continue
        session.pop(key)

    if delete == 'yes':
        ds.clearStore()
        return redirect(url_for('admin', delete='no', user='none'))
    if user != 'none':
        db.updateUserAuth(user)
        return redirect(url_for('admin', delete='no', user='none'))

    res = ds.storeContents()
    users = db.getAllUsers()

    return render_template('admin.html', title='Administration', store=res,
                            sessvar=sessVar, users=users, year=year)

#-------------------------------------------------------------------------------
# Route to the user registration page.
#-------------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    # This should never happen (navbar checks), but just in case...
    if session.get('username', None):
        msg = f'User {session.get("username")} is logged in. Sign out first.'
        flash(msg)
        return redirect(url_for('index'))

    form = RegisterForm()

    if form.validate_on_submit():
        # Store details on database, check for errors.
        msg = db.storeUser(form.username.data, form.email.data,
                           form.password.data)
        if msg:
            flash(msg)
            return redirect(url_for('register'))

        # No database errors, so continue to home page
        session['username'] = form.username.data
        session['email'] = form.email.data
        session['admin'] = 'n'
        msg = f'New User {form.username.data} is now registered'
        flash(msg)
        return redirect(url_for('index'))

    return render_template('register.html', title='Registration',
                            form=form, year=year)

#-------------------------------------------------------------------------------
