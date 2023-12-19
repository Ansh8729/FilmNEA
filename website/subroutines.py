from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import PyPDF4 
import PyPDF2

def send_email(subject, body, to_email, gmail_username, gmail_password):
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
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email could not be sent. Error: {str(e)}")

def NoSpaces(filename):
    if filename.count(" ") > 0:
        chars = list(filename)
        newname = ""
        for i in chars:
            if i != " ":
                newname += i
        return newname
    else:
        return filename
    
def IsPDF(filename): #Checks if the uploaded file is a PDF (the correct format)
    extension = (filename).split(".")
    ext = extension[1]
    if ext != "pdf":
        return False
    else:
        return True
    
def watermark(input_pdf, output_pdf, watermark): #Watermarks the pages
    watermark = PyPDF4.PdfFileReader(watermark)
    page_watermark=watermark.getPage(0)
    input_pdf_reader=PyPDF4.PdfFileReader(input_pdf)
    output_pdf_writer=PyPDF4.PdfFileWriter()
    for page in range(input_pdf_reader.getNumPages()):
        page=input_pdf_reader.getPage(page)
        page.mergePage(page_watermark)
        output_pdf_writer.addPage(page)
    with open(output_pdf, "wb") as output:
        output_pdf_writer.write(output)

def split_pdf(input, output, start, end): #Cuts the screenplay down to the pages selected by the user
    reader = PyPDF2.PdfReader(input)
    writer = PyPDF2.PdfWriter()
    for page_num in range(start,end): # loop through pages
        selected_page = reader.pages[page_num]
        writer.add_page(selected_page) # add/embedding of the page
    with open(output,"wb") as out:
        writer.write(out)

