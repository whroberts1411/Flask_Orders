"""
 Name:          dbAccess.py

 Purpose:       All the setup for database queries, etc., are in here. It will
                access the SQLiteDatabase module, so the Flask web code has no
                need to have any awareness of the database in use.
                It also has a number of utility functions not directly
                connected to database access.
                (could have picked a better name for the module)

 Author:        Bill

 Created:       28/07/2024

 Amended:

"""
#-------------------------------------------------------------------------------

import orders_app.SQLiteDatabase  as sld
sql = sld.SQLClass()
from orders_app import app
sql.db = app.config['DATABASE']

import datetime as dt
from datetime import datetime
from datetime import timedelta
import math
from pathlib import Path
from PIL import Image
from tinytag import TinyTag

# Methods for storing and checking hashed user passwords
from werkzeug.security import generate_password_hash, check_password_hash

#-------------------------------------------------------------------------------

def getCat():
    """ Return a list of category descriptions and food flags. """

    sql.query = 'Select CategoryDesc, Food From Category '
    sql.query += ' Order By CategoryDesc; '
    sql.values = []
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def getCatCounts():
    """ Get item counts for each category, with percentages. """

    sql.query = 'Select sum(Quantity) From OrderItems; '
    sql.values = []
    ret = sql.GetSQLData()
    total = int(ret[1][0])

    sql.query = 'Select c.CategoryDesc, sum(oi.Quantity) As "count" '
    sql.query += 'From OrderItems oi '
    sql.query += 'Inner Join Item i on oi.ItemId = i.ItemId Inner Join '
    sql.query += 'Category c On i.CategoryId = c.CategoryId Group By '
    sql.query += 'c.CategoryId Order By c.CategoryDesc; '
    sql.values = []
    ret = sql.GetSQLData()
    ret = ret[1:]

    # Calculate and add percentages to the list for each row
    for idx, item in enumerate(ret):
        pc = round(int(ret[idx][1]) * 100 / total, 2)
        ret[idx] = ret[idx] + [str(pc)]

    return ret

#-------------------------------------------------------------------------------

def getItemCosts():
    """ Get the cost of the top ten most expensive items, by total cost over
        all orders. """

    sql.query = 'Select oi.ItemId, i.ItemDesc, sum(oi.Quantity), '
    sql.query += 'round(sum(oi.TotalCost),2) '
    sql.query += 'From OrderItems oi Inner Join Item i On oi.ItemId = i.ItemId '
    sql.query += 'Group By oi.ItemId Order By sum(oi.TotalCost) Desc '
    sql.query += 'limit 10; '
    sql.values = []
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def getOrders(startDate, endDate):
    """ Return the orders in the supplied date range. """

    sql.query = 'Select o.OrderDate, o.OrderDesc, count(oi.OrderId) as '
    sql.query += '"Count", sum(oi.Quantity) as "Quantity", '
    sql.query += 'round(sum(oi.TotalCost), 2) as "TotalCost" '
    sql.query += 'From Orders o Inner Join OrderItems oi On o.OrderId '
    sql.query += '= oi.OrderId Where o.OrderDate Between ? and ? '
    sql.query += 'Group By oi.OrderId; '
    sql.values = [startDate, endDate]
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def getAllUsers():
    """ Return a list of all users (for the admin screen) """

    sql.query = 'Select Username, Email, upper(Admin) From Users '
    sql.query += 'Order by Username; '
    sql.values = []
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def updateUserAuth(username):
    """ Update the Admin column for the specified user. If it's currently set
        to 'n', change to 'y', and vice versa. """

    sql.query = 'Select Admin From Users Where Username = ?; '
    sql.values = [username]
    ret = sql.GetSQLData()

    newval = ''
    if ret[1][0] == 'n': newval = 'y'
    else: newval = 'n'

    sql.query = 'Update Users Set Admin = ? Where Username = ?; '
    sql.values = [newval, username]
    ret = sql.UpdateSQLData()

#-------------------------------------------------------------------------------

def getUser(username, password):
    """ Get user details from the database """

    msg = 'Error - Username and/or Password not found - Please retry'

    sql.query = 'Select Username, PasswordHash, Email, Admin From Users '
    sql.query += 'Where Username = ?; '
    sql.values = [username]
    ret = sql.GetSQLData()
    if len(ret) < 2:
        return msg

    if checkPassword(password, ret[1][1]):
        return msg
    else:
        return ret[1][2], ret[1][3]

#-------------------------------------------------------------------------------

def storeUser(username, email, password):
    """ Store user details on the database """

    msg = ''

    # check if username or email already in use - reject if it is.
    sql.query = 'Select Username From Users Where Username = ?;'
    sql.values = [username]
    ret = sql.GetSQLData()
    if len(ret) > 1:
        msg += 'Error - supplied username already exists'
        return msg

    sql.query = 'Select Email From Users Where Email = ?;'
    sql.values = [email]
    ret = sql.GetSQLData()
    if len(ret) > 1:
        msg += 'Error - supplied email already exists'
        return msg

    # OK so far - store the new user on the database.
    sql.query = 'Insert Into Users (Username, Email, PasswordHash, Admin)'
    sql.query += 'Values (?, ?, ?, ?); '
    sql.values = [username, email, generate_password_hash(password), 'n']
    ret = sql.UpdateSQLData()

    if isinstance(ret, int):
        return ''
    else:
        return ret

#-------------------------------------------------------------------------------

def checkPassword(password, passwordhash):
    """ Check the entered password against the stored password hash. """

    if check_password_hash(passwordhash, password):
         return ''
    else:
        return 'error'

#-------------------------------------------------------------------------------

def getLocations():
    """ Return a list of location names. """

    sql.query = 'Select LocationName From Location Order By LocationName; '
    sql.values = []
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def getLatLon(location):
    """ Get the latitude and longitude for the specified UK location. """

    sql.query = 'Select Latitude, Longitude From Location Where '
    sql.query += 'LocationName = ?; '
    sql.values = [location]
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def reformat(data):
    """ Split the API dictionary into separate lists. Each list will have
        sublists of [description, value] pairs, where the description will be
        suitable for screen output - e.g. 'vis_miles' --> 'Visibility (miles)'
    """

    daylength =getDayLength(data['astronomy']['astro']['sunrise'],
                            data['astronomy']['astro']['sunset'])
    wetC, wetF = calcWetBulb(data['current']['temp_c'],
                             data['current']['humidity'])

    loc = []
    loc.append(['Location', data['location']['name']])
    loc.append(['Region', data['location']['region']])
    loc.append(['Country', data['location']['country']])
    loc.append(['Timezone', data['location']['tz_id']])

    loc.append(['Latitude', str(data['location']['lat'])])
    loc.append(['Longitude', str(data['location']['lon'])])

    air = []
    air.append(['Carbon Monoxide', str(data['current']['air_quality']['co'])])
    air.append(['Nitrogen Dioxide', str(data['current']['air_quality']['no2'])])
    air.append(['Ozone', str(data['current']['air_quality']['o3'])])
    air.append(['Sulphur Dioxide', str(data['current']['air_quality']['so2'])])
    air.append(['Particulate Matter 10', str(data['current']['air_quality']['pm10'])])
    air.append(['Particulate Matter 2.5', str(data['current']['air_quality']['pm2_5'])])
    air.append(['Defra Index (UK)', str(data['current']['air_quality']['gb-defra-index'])])

    astro = []
    astro.append(['Sunrise', data['astronomy']['astro']['sunrise']])
    astro.append(['Sunset', data['astronomy']['astro']['sunset']])
    astro.append(['Day Length', daylength + ' hours'])
    astro.append(['Moonrise', data['astronomy']['astro']['moonrise']])
    astro.append(['Moonset', data['astronomy']['astro']['moonset']])
    astro.append(['Moon Phase', data['astronomy']['astro']['moon_phase']])
    astro.append(['Moon Illumination (%)', str(data['astronomy']['astro']['moon_illumination'])])

    met = []
    met.append(['Currently', data['current']['condition']['text']])
    met.append(['Cloud Cover (%)', str(data['current']['cloud'])])
    met.append(['Temperature (C)', str(data['current']['temp_c'])])
    met.append(['Feels Like (C)', str(data['current']['feelslike_c'])])
    met.append(['Wind Chill (C)', str(data['current']['windchill_c'])])
    met.append(['Wet Bulb Temp (C)', str(wetC)])
    met.append(['Dew Point (C)', str(data['current']['dewpoint_c'])])
    met.append(['Relative Humidity (%)', str(data['current']['humidity'])])
    met.append(['Pressure (mb)', str(data['current']['pressure_mb'])])
    met.append(['Precipitation (mm)', str(data['current']['precip_mm'])])
    met.append(['Visibility (km)', str(data['current']['vis_km'])])
    met.append(['Wind Direction', str(data['current']['wind_dir'])])
    met.append(['Wind Direction (deg)', str(data['current']['wind_degree'])])
    met.append(['Wind Speed (kph)', str(data['current']['wind_kph'])])
    met.append(['Wind Gusts (kph)', str(data['current']['gust_kph'])])
    met.append(['UV Index (1 - 9+)', str(data['current']['uv'])])

    imp = []
    imp.append(['Currently', data['current']['condition']['text']])
    imp.append(['Cloud Cover (%)', str(data['current']['cloud'])])
    imp.append(['Temperature (F)', str(data['current']['temp_f'])])
    imp.append(['Feels Like (F)', str(data['current']['feelslike_f'])])
    imp.append(['Wind Chill (F)', str(data['current']['windchill_f'])])
    imp.append(['Wet Bulb Temp (F)', str(wetF)])
    imp.append(['Dew Point (F)', str(data['current']['dewpoint_f'])])
    imp.append(['Relative Humidity (%)', str(data['current']['humidity'])])
    imp.append(['Pressure (ins)', str(data['current']['pressure_in'])])
    imp.append(['Precipitation (ins)', str(data['current']['precip_in'])])
    imp.append(['Visibility (miles)', str(data['current']['vis_miles'])])
    imp.append(['Wind Direction', str(data['current']['wind_dir'])])
    imp.append(['Wind Direction (deg)', str(data['current']['wind_degree'])])
    imp.append(['Wind Speed (mph)', str(data['current']['wind_mph'])])
    imp.append(['Wind Gusts (mph)', str(data['current']['gust_mph'])])
    imp.append(['UV Index (1 - 9+)', str(data['current']['uv'])])

    # Concatenate the metric and imperial lists, row-wise
    res = list(sub1 + sub2 for sub1, sub2 in zip(met, imp))

    return loc, air, astro, res

#-------------------------------------------------------------------------------

def getDayLength(start, end):
    """ Calculate the interval between the provided start and end times, as a
        decimal hour value. They will be strings in the format '09:35 PM' """

    # Convert to 24hr format
    start = start.replace(' ', '')
    start = datetime.strptime(start, '%I:%M%p').strftime('%H:%M')
    end = end.replace(' ', '')
    end = datetime.strptime(end, '%I:%M%p').strftime('%H:%M')

    # Get the difference
    tdelta = datetime.strptime(end, '%H:%M') - datetime.strptime(start, '%H:%M')
    hours = (tdelta.seconds/3600)

    return str(round(hours, 2))

#-------------------------------------------------------------------------------

def calcWetBulb(tempC, humidity):
    """ Calculate the wet bulb temperature in both centigrade and farenheit.
        Return the values rounded to 2 decimal places. Input parameters
        are float values. """

    a = tempC * math.atan(0.151977 * (humidity + 8.313659) ** 0.5)
    b = math.atan(tempC + humidity) - math.atan(humidity - 1.676331)
    c = 0.00391838 * humidity ** (1.5) * math.atan(0.023101 * humidity)
    d = -4.686035
    wetbulbC = a + b + c + d

    # First is Centigrade, second is Farenheit
    return str(round(wetbulbC, 2)), str(round((wetbulbC * 1.8 + 32), 2))

#-------------------------------------------------------------------------------

def getTables():
    """ Get schema details for Tables, returning table names and row counts.
        Exclude the sqlite system table and any tables with 'backup' in the
        name. """

    tables = []
    ret = sql.getTables()

    for table in ret[1:]:
        sql.query = 'Select count(*) From ' + table[0] + '; '
        sql.values = []
        tot = sql.GetSQLData()
        if (not table[0].startswith('sqlite') and
            table[0].lower().count('backup') < 1):
            tables.append([table[0], tot[1][0]])

    return tables

#-------------------------------------------------------------------------------

def getViews():
    """ Get schema details for Views. """

    views = []
    ret = sql.getViews()

    return ret[1:]

#-------------------------------------------------------------------------------

def getTableDets(name, option):
    """ Return either the columns in the table (option='table') or the first 15
        rows of data from the table (option='rows').  """

    fmt = ''

    if option == 'table':
        ret = sql.getColumnList(name)
    elif option == 'rows':
        ret = sql.getTableData(name, 15)
    elif option == 'view':
        ret = sql.getTableData(name, 15)
        view = sql.getViewDefinition(name)
        fmt = formatView(view[1:][0])

    # For the 'ret' result sets the first row (column names) WILL be returned.
    # The 'fmt' result is a html-formatted string (not a list).
    return ret, fmt

#-------------------------------------------------------------------------------

def formatView(data):
    """ The view definition code will be used in an html template, so all
        the embedded control characters need to be replaced with the html
        equivalent. The 'data' argument is a list with a single string
        entry.  """

    temp = data[0]
    temp = temp.replace('\r\n\r\n', '<br>')
    temp = temp.replace('\r\n', '<br>')
    temp = temp.replace('\t', '    ')
    return temp

#-------------------------------------------------------------------------------

def getThumbnails(dirName, pixels):
    """ Return a list of all thumbnail images (full paths) in the specified
        folder. Create thumbnails for any images that don't already have them.
        Only files with jpg or jpeg extensions will be processed. """

    thumbs = []
    size = (int(pixels), int(pixels))
    l1 = list(Path(dirName).glob('*.*'))

    for f in l1:
        imgExt = str(Path(f).suffix)
        if not imgExt.lower() in ('.jpg', '.jpeg'):
            continue

        fname = Path(f).stem
        fpath = str(Path(f).parent.absolute())
        fpath = fpath.replace('\\', '/') + '/'
        thumb = fname + '_thumb' + imgExt

        if Path(fpath + thumb).is_file():
            continue

        if '_thumb' in str(f):
            thumbs.append([str(f), fname.replace('_thumb','') + imgExt])
        else:
            im = Image.open(f)
            im.thumbnail(size)
            im.save(fpath + thumb)
            thumbs.append([fpath + thumb, fname.replace('_thumb','') + imgExt])

    return thumbs

#-------------------------------------------------------------------------------

def storeNewImages(images, pixels):
    """ Store the new image details on the database (they are already in
        filestore). Create thumbnails for them all with a size of "pixels". """

    thumbs = []
    size = (int(pixels), int(pixels))
    msg = 'This is a new image. Please add a description.'

    for image in images:
        f = Path(image)
        imgExt = str(Path(f).suffix)
        fname = Path(f).stem
        #fpath = str(Path(f).parent.absolute()) + '\\'
        fpath = str(Path(f).parent.absolute()) + '/'
        fpath = fpath.replace('\\', '/')
        thumb = fname + '_thumb' + imgExt

        im = Image.open(f)
        im.thumbnail(size)
        im.save(fpath + thumb)

        mod = datetime.fromtimestamp(f.stat().st_mtime, tz=dt.timezone.utc)
        mod = mod.strftime('%d/%m/%Y %H:%M')

        sql.query = 'Select ImageId From Image Where ImageName = ?;'
        sql.values = [str(f)]
        ret = sql.GetSQLData()

        if len(ret) < 2:
            sql.query = 'Insert Into Image (ImageName, Description, DateAdded) '
            sql.query += 'Values (?, ?, ?); '
            sql.values = [str(f).replace('\\','/'), msg, mod]
            ret = sql.UpdateSQLData()

#-------------------------------------------------------------------------------

def getImageDetails():
    """ Return a list of stored image details from the database. This needs to
        be reformatted as lists of 4 values for output to the web template. """

    sql.query = 'Select ImageName, Description, DateAdded From Image '
    sql.query += 'Order By ImageName; '
    sql.values = []
    ret = sql.GetSQLData()
    fmt = imgFormat(ret[1:])
    return fmt

#-------------------------------------------------------------------------------

def imgFormat(data):
    """ The input data will have image name (full path WITHOUT _thumb),
        description and date. Need to return image name, full path WITH _thumb,
        image name alone (without _thumb), description and date. """

    amended = []

    for item in data:
        f = Path(item[0])
        shortName = Path(f).stem + str(Path(f).suffix)
        thumbName = item[0].replace('.', '_thumb.')
        amended.append([thumbName, shortName, item[1], item[2]])
    return amended

#-------------------------------------------------------------------------------

def populateImageTable(dir):
    """ For initial setup only. Only store the original images, not the
        thumbnails we have created. This function will only be called
        from <main>, not from the website.  """

    ret = getThumbnails(dir, '640')
    msg = 'This is a new image. Please add a description.'
    for thumb in ret:
        if '_thumb' in (thumb[0]):
            thumb[0] = thumb[0].replace('_thumb','')

        f = Path(thumb[0])
        mod = datetime.fromtimestamp(f.stat().st_mtime, tz=dt.timezone.utc)
        mod = mod.strftime('%d/%m/%Y %H:%M')

        sql.query = 'Insert Into Image (ImageName, Description, DateAdded) '
        sql.query += 'Values (?, ?, ?); '
        sql.values = [thumb[0], msg, mod]
        ret = sql.UpdateSQLData()

#-------------------------------------------------------------------------------

def deleteImage(image):
    """ Delete an image from the database. """

    image = image.replace('_thumb', '')
    sql.query = 'Delete From Image Where ImageName = ?;'
    sql.values = [image]
    res = sql.UpdateSQLData()
    return res

#-------------------------------------------------------------------------------

def getImageByName(name):
    """ Get the requested image details (matching on name). """

    sql.query = 'Select ImageName, Description, DateAdded From Image '
    sql.query += 'Where ImageName = ?; '
    sql.values = [name]
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def updateImage(oldname, name, desc):
    """ Update the image details, matching on "oldname". """

    sql.query = 'Update Image Set ImageName = ?, Description = ? '
    sql.query += 'Where ImageName = ?; '
    sql.values = [name, desc, oldname]
    ret = sql.UpdateSQLData()
    return ret

#-------------------------------------------------------------------------------

def storeAudio(tracks):
    """ Store the details of the supplied audio file(s) on the database. Uses
        the TinyTag library to get the ID3 tag information from the file.
        NOTE: TinyTag fails with a 'file not found' error if the filename is
              passed as a Windows path (with '\' separators). They need to
              be changed to '/', then all is well. """

    for track in tracks:
        track = track.replace('\\', '/')
        tag = TinyTag.get(track)
        # Convert decimal seconds to a 'MM:SS' string
        minutes = int(tag.duration / 60)
        seconds = int(tag.duration - minutes * 60)
        trackLength = f'{minutes}:{seconds}'

        sql.query = 'Insert Into Music (Filename, Title, Artist, Album, Year, '
        sql.query += 'Duration) Values (?, ?, ?, ?, ?, ?); '
        sql.values = [track, tag.title, tag.artist, tag.album, tag.year,
                      trackLength]
        ret = sql.UpdateSQLData()

#-------------------------------------------------------------------------------

def getAudio():
    """ Return a list of all music details. """

    sql.query = 'Select Filename, Title, Artist, Album, Year, Duration '
    sql.query += 'From Music Order By Title; '
    sql.values = []
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def deleteAudio(fname):
    """ Delete the details of the requested audio file from the database,
        matching on the music track file name. """

    sql.query = 'Delete From Music Where Filename = ?; '
    sql.values = [fname]
    ret = sql.UpdateSQLData()
    return ret

#-------------------------------------------------------------------------------

def storeVideo(data, locn, source):
    """ Store the details for a new video on the database. 'data' will hold the
        new details, and 'source' will be one of 'yt' or 'mp4'. If 'yt', it
        will be the return data from the YouTube API. 'locn' will be either
        the YouTube url for the video, or the server file path to the mp4
        video file. """

    if source == 'yt':
        title = data['items'][0]['snippet']['title']
        dat = data['items'][0]['snippet']['publishedAt'][:10]
    else:
        title = data
        f = Path(locn)
        dat = datetime.fromtimestamp(f.stat().st_mtime, tz=dt.timezone.utc)
        dat = dat.strftime('%d/%m/%Y %H:%M')

    sql.query = 'Select VideoId From Video Where Key = ?; '
    sql.values = [locn]
    ret = sql.GetSQLData()
    if len(ret) > 1: return ret

    sql.query = 'Insert Into Video (Key, Title, VideoDate, VideoType) Values '
    sql.query += '(?, ?, ?, ?); '
    sql.values = [locn, title, dat, source]
    ret = sql.UpdateSQLData()
    return ret

#-------------------------------------------------------------------------------

def getVideo():
    """ Get the video details from the database. """

    sql.query = 'Select Key, Title, VideoDate, VideoType From Video '
    sql.query += 'Order By Title; '
    sql.values = []
    ret = sql.GetSQLData()
    return ret[1:]

#-------------------------------------------------------------------------------

def deleteVideo(key):
    """ Delete the requested video from the database. """

    sql.query = 'Delete From Video Where Key = ?; '
    sql.values = [key]
    ret = sql.UpdateSQLData()
    return ret

#-------------------------------------------------------------------------------

def main():
    """ Testing code will go here. """

    ret = getAllUsers()
    print(ret)
    return

    res = storeAudio(["static\\music\\Black Dog.mp3"])
    print(res)
    return

    audio = ["J:\Desktop\music\Black Dog.mp3","J:\Desktop\music\Cherry Bomb.mp3",
         "J:\Desktop\music\She's A Woman.mp3",
         "J:\Desktop\music\Village Green Preservation Society.mp3",
        "J:\Desktop\music\I Wish I Was A Punk Rocker (With Flowers In My Hair).mp3",
        "J:\Desktop\music\December, 1963 (Oh What A Night!).mp3"]

    for track in audio:
        storeAudio(track)
        print('------------------------------')

    return

    ret = getItemCosts()
    for item in ret:
        print(item)
    return

    images = ['static/images/IMG_2786.JPG', 'static/images/IMG_2798.JPG']
    ret = storeNewImages(images, '640')
    print(ret)

    return
    from subprocess import Popen
    Popen('pdoc dbAccess.py -o ./docs')
    print('HTML docs produced for this module')

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------
