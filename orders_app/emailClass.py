"""
 Name:          emailClass

 Purpose:       Implement email processing using the Python built in library
                smtp. This requires a Google App Password to work, as Google
                has recentrly changed its policy regarding untrusted apps. The
                emails can be formatted as either plain text or html.

                Google App Password :  hixciexnklppydmk

 Author:        Bill

 Created:       16/12/2022

 Amended:       19/12/2022
                Add a new property for attachments required, which will be a
                list containing file names. These will be added to the email
                as attachments.

 *** NOTE ***
 In order for this module to be availabe in any project (without needing to
 copy it) the main version is located in the N:/Utilities folder. Also
 need to set the environment variable PYTHONPATH to the path to the folder.

 ******************************************************
 ***** THIS IS A LOCAL COPY FOR THE FLASK WEBSITE *****
 ******************************************************

"""

#-------------------------------------------------------------------------------

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import mimetypes

#-------------------------------------------------------------------------------

class EmailClass:
    """ Send emails using the Python smtp built-in library. """

    def __init__(self):
        """ Instantiate and initialise the class object and properties. """

        self.gmailPassword = 'hixciexnklppydmk'
        self.gmailUser = 'whroberts1411@gmail.com'
        self.__sentFrom = 'whroberts@hotmail.com'
        self.__to = []
        self.__subject = None
        self.__body = None
        self.__html = True
        self.__attachment = []

#-------------------------------------------------------------------------------
# Public Setter and Getter methods for selected input and output values.
# NB - both required if properties are write or read/write. But only the
#      getter required if the property is read-only.
#-------------------------------------------------------------------------------

    @property
    def sentFrom(self):
        return self.__sentFrom
    @sentFrom.setter
    def sentFrom(self, value):
        self.__sentFrom = value

    @property
    def to(self):
        return self.__to
    @to.setter
    def to(self, value):
        self.__to = value

    @property
    def subject(self):
        return self.__subject
    @subject.setter
    def subject(self, value):
        self.__subject = value

    @property
    def body(self):
        return self.__body
    @body.setter
    def body(self, value):
        self.__body = value

    @property
    def html(self):
        return self.__html
    @html.setter
    def html(self, value):
        self.__html = value

    @property
    def attachment(self):
        return self.__attachment
    @attachment.setter
    def attachment(self, value):
        self.__attachment = value

#-------------------------------------------------------------------------------
# PUBLIC CLASS METHODS
#-------------------------------------------------------------------------------

    def sendMail(self):
        """ Send an email via Google, using the details from the class property
            values passed in by the calling application. Note that the Google
            user and app password are fixed and cannot be changed. """

        # There may be more than one recipient - but passed as a list anyway,
        # so split into a text string.
        recip = ', '.join(self.to)

        # Set up the email contents
        eText = MIMEMultipart('alternative')
        eText['Subject'] = self.subject
        eText['From'] = self.sentFrom
        eText['To'] = recip

        # The body of the email will be either plain text or html-formatted
        if self.html:
            msg = MIMEText(self.body, 'html')
        else:
            msg = MIMEText(self.body, 'plain')
        eText.attach(msg)

        # Do we have a file attachment (or attachments) to send?
        if self.attachment:
            # Loop through each attachment...
            for currFile in self.attachment:
                fType = self.TranslateAttachmentType(currFile)

                if fType == 'text':
                    tmp = MIMEText(open(currFile).read())
                elif fType == 'image':
                    tmp = MIMEImage(open(currFile, 'rb').read())
                else:
                    tmp = MIMEApplication(open(currFile, 'rb').read())

                tmp.add_header('Content-Disposition', 'attachment',
                                filename=currFile)
                eText.attach(tmp)

        # Everything ready, so try and send the email...
        try:
            smtpServer = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            smtpServer.ehlo()
            smtpServer.login(self.gmailUser, self.gmailPassword)
            smtpServer.sendmail(self.sentFrom, self.to, eText.as_string())
            smtpServer.close()
            res = 'Email sent successfully!'
        except Exception as ex:
            res = f'Something went wrong\n {ex}'

        return res

#-------------------------------------------------------------------------------
# PRIVATE CLASS METHODS
#-------------------------------------------------------------------------------

    def __str__(self):
        """ Print brief details of what this class does.
        Usage : em = emailClass.EmailClass()
                print(em)
        """

        desc = 'Class to send an email via the Gmail server using smtp'
        return desc

#-------------------------------------------------------------------------------

    def __repr__(self):
        """ Print brief details of what this class does.
        Usage : em = emailClass.EmailClass()
                print(repr(em))
        """

        desc = 'EmailClass()'
        return desc

#-------------------------------------------------------------------------------

    def TranslateAttachmentType(self, currFile):
        """ Try and determine the mime type of the attachment. Return either
            text, image or application. """

        # Do we have a file extension?
        if '.' in currFile:
            tmp =mimetypes.guess_type(currFile)[0]
            ret = tmp.split('/')[0]
        else:
            # No file extension, so return the default mime type
            ret = 'application'

        return ret.lower()

#-------------------------------------------------------------------------------

def main():
    """ Entry point for this class """

    return
    from subprocess import Popen
    Popen('pdoc emailClass.py -o ./docs')
    print('HTML docs produced for this module')

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------
