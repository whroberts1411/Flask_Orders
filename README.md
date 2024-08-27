# Flask_Orders

 This is the first time I've used Flask for building a website, so it is mainly 
a collection of pages to demonstrate various things that I would want to do on
a "proper" website. The website doesn't use any Flask add-ons, except for 
forms-wtf. All other functionality has been built from internal code on the
website. The only other imports it uses (other than those built in to python)
are :

- matplotlib
- tinytag (for extracting ID3 tags from mp3 files)
- Bootstrap v5.3.3., on the HTML template side, 

## Techniques used in the website

1. User Authentication, with log in, log out and registration pages. A decorator
function is also used to provide @login_required functionality to limit user access
to certain routes (depending on authorisation). 
2. The full range of database functions are used (CRUD), supported by a separate 
SQL database module. The site does **not** use the Flask ORM. It uses a SQLite database.
3. Email sending, with multiple recipients and multiple file attachments supported.
4. Visual display of database data using matplotlib.
5. Interfacing with external APIs to provide weather information for a selection
of UK locations, and to access video data from YouTube.
6. Uploading and display of user-selected images, also producing smaller-sized 
versions for web display. Options to delete images, and also to use them as 
background wallpaper for the site.
7. Uploading user-selected music files, which can be listed, played and deleted.
8. Uploading user-selected video files, and selection of videos from YouTube.
Both formats (mp4 & YouTube) can be played on-screen.
9. Implementation of a server-side session storage class, to get around the size
limitations of the built-in Flask session object.
10. Pagination for screens displaying large amounts of data from the database.
11. Making table rows active, allowing drill-down, etc., for database data.

Comparing Flask with Django, it certainly has a much shallower learning curve, 
but seems to offer much of the functionality with a bit less hassle and coding.
The Flask url routing mechanism is a lot easier to code and understand, in my
opinion.
