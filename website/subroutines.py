from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import PyPDF4 
import PyPDF2
import flask

def SendEmail(subject, body, to_email, gmail_username, gmail_password): # Sends an email
    # Create a MIMEText object to represent the email body
    message = MIMEMultipart()
    message.attach(MIMEText(body, 'plain'))

    message['Subject'] = subject
    message['From'] = gmail_username
    message['To'] = to_email

    try:
        # Establish a connection to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        # Starts TLS encryption
        server.starttls()
        # Logs in to the NoReply gmail account
        server.login(gmail_username, gmail_password)
        # Sends the email
        server.sendmail(gmail_username, to_email, message.as_string())
        # Closes the SMTP server connection
        server.quit()
        flask.flash("Email sent successfully!", category='success')  
    except Exception as error:
        flask.flash(f"Email could not be sent. Error: {str(error)}", category="error")

def NoSpaces(filename): # Removes spaces from a file's name
    if filename.count(" ") > 0:
        chars = list(filename)
        newname = ""
        for i in chars:
            if i != " ":
                newname += i
        return newname
    else:
        return filename
    
def IsPDF(filename): # Checks if a file is in the PDF format
    extension = (filename).split(".")
    ext = extension[1]
    if ext != "pdf":
        return False
    else:
        return True
    
def Watermark(InputPDF, OutputPDF, watermark): # Watermarks the pages of a given PDF
    watermark = PyPDF4.PdfFileReader(watermark)
    PageWatermark = watermark.getPage(0)
    InputFile = PyPDF4.PdfFileReader(InputPDF)
    OutputFile = PyPDF4.PdfFileWriter()
    for page in range(InputFile.getNumPages()):
        page = InputFile.getPage(page)
        page.mergePage(PageWatermark)
        OutputFile.addPage(page)
    with open(OutputPDF, "wb") as output:
        OutputFile.write(output)

def ExtractPDF(input, output, start, end): # Extracts a specific range of pages from a PDF
    reader = PyPDF2.PdfReader(input)
    writer = PyPDF2.PdfWriter()
    for page_num in range(start,end): 
        selected_page = reader.pages[page_num]
        writer.add_page(selected_page)
    with open(output,"wb") as out:
        writer.write(out)

