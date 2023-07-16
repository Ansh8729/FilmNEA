from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, TextAreaField, SelectField, IntegerField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired
import PyPDF4 
from PyPDF4 import PdfFileReader, PdfFileWriter
import shutil
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename
import uuid as uuid
from . import db

views = Blueprint("views", __name__)

class UploadFileForm(FlaskForm): #Allows users to input the data needed to upload their screenplay.
    file = FileField("File", validators=[InputRequired()])
    start = IntegerField("Start page: ", validators=[InputRequired()])
    end = IntegerField("End page: ", validators=[InputRequired()])
    submit = SubmitField("Upload File")

def AreThereSpaces(filename): #Checks if the name of the file they have uploaded has any spaces
    spaces = 0
    chars = list(filename)
    for i in range(0,len(chars)):
        if chars[i] == ' ':
            spaces += 1
    if spaces > 0:
        flash("Your filename CANNOT have spaces!")
        for i in range(0,len(chars)):
            if chars[i] == ' ':
                chars[i] = "_"
        newname = "".join(chars) 
        os.remove(newname)
        spaces = 0
        return True
    else:
        return False
    
def IsPDF(filename): #Checks if the uploaded file is a PDF (the correct format)
    extension = (filename).split(".")
    ext = extension[1]
    if ext != "pdf":
        flash("Your file is not a PDF!")
        os.remove(filename)

def ValidPageNums(filename, start, end): #Checks if the program can output the correct pages (no page numbers going over the length of the screenplay and only 10 pages can be uploaded)
    file2 = PyPDF2.PdfReader(filename)
    nums = len(file2.pages)
    if end > nums:
        flash("Your screenplay doesn't have "+str(end)+" pages!")
        os.remove(filename)
        return False
    elif end-start > 10:
        flash("You can't upload more than 10 pages!")
        os.remove(filename)
        return False

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

@views.route("/")
@views.route("/home")
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route("/profilepage")
@login_required
def profilepage():
    user = Users.query.filter_by(username = current_user.username).first()
    if user.accounttype == 1:
        details = Screenwriters.query.filter_by(userid = user.id).first()
    elif user.accounttype == 2:
        details = Producers.query.filter_by(userid = user.id).first()

    return render_template("profilepage.html", user=current_user, details1=user, details2=details)

@views.route("/pageeditor", methods=['GET', 'POST'])
@login_required
def pageeditor():
    if request.method == "POST":
        file = request.form.get('profilepic')
        picturefilename = secure_filename(file.filename)
        picname = str(uuid.uuid1()) + "_" + picturefilename
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],picname)) 
        shutil.move(picname,'static/files')
        query = Screenwriters.query.filter_by(username = current_user.username).first()
        query.profilepic = picname
        query.biography = form.biography.data
        db.session.commit()
        flash("Edits made!")
        return render_template("profilepage.html", user=current_user)
    return render_template("pageeditor.html", form=form, user=current_user)

@views.route("/post", methods=['GET', 'POST'])
@login_required
def post():
    form = UploadFileForm()
    if form.validate_on_submit():
        # The data is grabbed from the form
        file = form.file.data 
        start = form.start.data
        end = form.end.data
        # The file is saved to the folder
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) 
        if AreThereSpaces(file.filename) == True:
            flash("There are spaces in the file name!", category='error')
        else:
            if IsPDF(file.filename) == False:
                flash("Upload a PDF!", category='error')
            else:
                if ValidPageNums(file.filename, start, end) == False:
                    flash("Invalid page range!", category='error')
                else:
                    PyPDF4.PdfFileReader(file.filename)
                    watermark(input_pdf=file.filename,output_pdf="watermarked.pdf", watermark="watermark.pdf")
                    os.remove(file.filename)
                    split_pdf(input="watermarked.pdf",output="finalfile.pdf",start=start, end=end)
                    os.remove("watermarked.pdf")
                    shutil.move("finalfile.pdf",'static/files')
                    return render_template("home.html", user=current_user)

    return render_template('create_post.html', form=form, user=current_user)
