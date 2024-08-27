"""
 Name:          forms.py

 Purpose:       Module to hold the classes for the Flask web forms.

 Author:        Bill

 Created:       02/08/2024
"""

#-------------------------------------------------------------------------------

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                    TextAreaField, DateField)
from wtforms.validators import DataRequired, EqualTo, Length, Optional
from flask_wtf.file import (FileField, FileRequired, MultipleFileField,
                            FileAllowed)
from datetime import datetime

#-------------------------------------------------------------------------------

class DateRangeForm(FlaskForm):
    """ Get a date range for data selection. """

    startDate = DateField('Start Date', validators=[DataRequired()],
                            default=datetime(2023,1,1))
    endDate = DateField('End Date', validators=[DataRequired()],
                            default=datetime.now())
    #submit = SubmitField('Get Orders')

#-------------------------------------------------------------------------------

class ImageBrowseForm(FlaskForm):

    newImages = MultipleFileField('Select New Image(s) :', validators=[
        FileAllowed(['jpg','jpeg','JPG','JPEG'], 'Images Only (jpg)!')])

#-------------------------------------------------------------------------------

class MusicBrowseForm(FlaskForm):

    newTracks = MultipleFileField('Select New Music Tracks(s) :', validators=[
        FileAllowed(['mp3','MP3'], 'MP3 music tracks Only!')])

#-------------------------------------------------------------------------------

def getImageEditForm(imgName, imgDesc):
    """ Enable run-time setting of a form field's default value. """

    class ImageEditForm(FlaskForm):
        """ Edit the image name and description. """

        name = StringField('Image Name :', validators=[DataRequired()],
                            default=imgName)
        desc = TextAreaField('Description :', validators=[DataRequired()],
                            default=imgDesc)

    return ImageEditForm

#-------------------------------------------------------------------------------

class VideoLoadForm(FlaskForm):
    """ Get either a YouTube video (by videoId) or a regular MP4 video
        (uploaded to the static/video/ folder). """

    ytident = StringField('New YouTube Video ID :', validators=[Optional()])
    title = StringField('Title for New MP4 Video : ', validators=[Optional()])
    newVideo = FileField('', validators=[FileAllowed(['mp4','MP4'],
                            'MP4 video files Only!')])

    def validate(self, extra_validators=None):
        # Check that one or other of the input fields is entered...
        if not super().validate():
            return False
        result = True
        if (not self.ytident.data and not self.title.data):
            self.ytident.errors.append('Please enter either ID or Title.')
            self.title.errors.append('Please enter either ID or Title.')
            result = False
        if (self.ytident.data and self.title.data):
            self.ytident.errors.append('Please enter either ID or Title, not both.')
            self.title.errors.append('Please enter either ID or Title, not both.')
            result = False
        if (self.title.data and not self.newVideo.data):
            self.newVideo.errors.append('Select an MP4 Video file.')
            result = False
        return result

#-------------------------------------------------------------------------------

def getEmailForm(strValue):
    """ Enable run-time setting of a form field's default value. """

    class EmailForm(FlaskForm):
        """ Send a user-generated email. """

        sender = StringField('Sender Email', default=strValue,
                             validators=[DataRequired()])
        recipient = StringField('Recipient(s) Email', validators=[DataRequired()])
        subject = StringField('Subject', validators=[DataRequired()])
        body = TextAreaField('Email Text', validators=[DataRequired()])
        attachment = MultipleFileField('File Attachment(s)')
        submit = SubmitField('Send Email')

    return EmailForm

#-------------------------------------------------------------------------------

class LoginForm(FlaskForm):
    """ User login form. """

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    #remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

#-------------------------------------------------------------------------------

class RegisterForm(FlaskForm):
    """ User Registration Form. """

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                    DataRequired(),
                    EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Register')

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
