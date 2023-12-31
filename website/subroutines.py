from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import flask

def SendEmail(subject, body, to_email, gmail_username, gmail_password): 
    # Create a MIMEText object to represent the email body
    message = MIMEMultipart()
    message.attach(MIMEText(body, 'plain'))

    message['Subject'] = subject
    message['From'] = gmail_username
    message['To'] = to_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_username, gmail_password)
        server.sendmail(gmail_username, to_email, message.as_string())
        server.quit()
        flask.flash("Email sent successfully!", category='success')  
    except Exception as error:
        flask.flash(f"Email could not be sent. Error: {str(error)}", category="error")

def NoSpaces(filename): # Removes spaces from a file's name
    if filename.count(" ") > 0:
        chars = list(filename)
        newname = ""
        for char in chars:
            if char != " ":
                newname += char 
        return newname
    else:
        return filename

def IncludesAtSymbol(handle):
    handle = list(handle)
    if handle[0] == "@":
        return True
    else:
        return False

    




