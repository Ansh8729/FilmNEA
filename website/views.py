from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Competitions, Submissions, Screenplays
from flask_wtf import FlaskForm
from wtforms import widgets, RadioField, StringField, SubmitField, FileField, TextAreaField, SelectField, IntegerField, DateField, SelectMultipleField
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
from dateutil.parser import parse
from datetime import date, timedelta

views = Blueprint("views", __name__)

def convert_to_datetime(input_str, parserinfo=None):
    return parse(input_str, parserinfo=parserinfo)

'''
class UploadFileForm(FlaskForm): #Allows users to input the data needed to upload their screenplay.
    file = FileField("File", validators=[InputRequired()])
    start = IntegerField("Start page: ", validators=[InputRequired()])
    end = IntegerField("End page: ", validators=[InputRequired()])
    submit = SubmitField("Upload File")
'''
    
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

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
    posts = Screenplays.query.all()
    return render_template("home.html", user=current_user, posts=posts)

@views.route("/profilepage")
@login_required
def profilepage():
    userdetails = Users.query.filter_by(username = current_user.username).first()
    return render_template("profilepage.html", user=current_user, userdetails=userdetails)

@views.route("/pageeditor", methods=['GET', 'POST'])
@login_required
def pageeditor():
    userdetails = Users.query.filter_by(username = current_user.username).first()
    if request.method == "POST":
        file = request.files['profilepic']
        picturefilename = secure_filename(file.filename)
        picname = str(uuid.uuid1()) + "_" + picturefilename
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',picname)) 
        shutil.move(picname,'static/images')
        query = Users.query.filter_by(username = current_user.username).first()
        query.profilepic = picname
        query.biography = request.form.get('bio')
        db.session.commit()
        flash("Edits made!")
        return render_template("profilepage.html", user=current_user, userdetails=userdetails)
    return render_template("pageeditor.html", user=current_user, userdetails=userdetails)

@views.route("/post", methods=['GET', 'POST'])
@login_required
def post():
    userdetails = Users.query.filter_by(username = current_user.username).first()
    if userdetails.accounttype == 2:
        if request.method == "POST":
            producerdetails = Producers.query.filter_by(userid = userdetails.id).first()
            num = producerdetails.producerid
            deadline=str(request.form.get("date"))
            date = convert_to_datetime(deadline)
            newcomp = Competitions(producerid = num, title=request.form.get("title"), brief=request.form.get("brief"), deadline=date)
            db.session.add(newcomp)
            db.session.commit()
            flash("Competition created!")
            return redirect(url_for('views.competitions'))
        return render_template('create_post.html', user=current_user, userdetails=userdetails)
    
    elif userdetails.accounttype == 1:
        if request.method == "POST":
            # The data is grabbed from the form
            title = request.form.get("title")
            logline = request.form.get("logline")
            message = request.form.get("message")
            file = request.files['screenplay']
            start = int(request.form.get("start"))
            end = int(request.form.get("end"))
            # The file is saved to the folder
            scriptname = secure_filename(file.filename) 
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
            if IsPDF(file.filename) == False:
                flash("Upload a PDF!", category='error')
            else:
                if ValidPageNums(file.filename, start, end) == False:
                    flash("Invalid page range!", category='error')
                else:
                    PyPDF4.PdfFileReader(scriptname)
                    watermark(input_pdf=file.filename,output_pdf="watermarked.pdf", watermark="watermark.pdf")
                    os.remove(file.filename)
                    newname = str(uuid.uuid1()) + "_" + "finalfile.pdf"
                    split_pdf(input="watermarked.pdf",output=newname ,start=start, end=end)
                    os.remove("watermarked.pdf")
                    shutil.move(newname,'static/images')
                    currentwriter = Screenwriters.query.filter_by(userid = current_user.id).first()
                    newpost = Screenplays(writerid = currentwriter.userid, title=title, logline=logline, message=message, screenplay=newname)
                    db.session.add(newpost)
                    db.session.commit()
                    posts = Screenplays.query.all()
                    return render_template("home.html", user=current_user, posts=posts)
        return render_template('create_post.html', user=current_user, userdetails=userdetails)

'''
        if AreThereSpaces(file.filename) == True:
            flash("There are spaces in the file name!", category='error')
        else:
'''

@views.route("/competitions", methods=['GET', 'POST'])
@login_required
def competitions():
    userdetails = Users.query.filter_by(username = current_user.username).first()
    comps2 = Competitions.query.all()
    subs = Submissions.query.all()
    for comp in comps2:
        subs2 = Submissions.query.filter_by(compid = comp.compid)
        comp.submissionnum = subs2.count()
        db.session.commit()
    comps = Competitions.query.order_by(Competitions.submissionnum.desc())
    if request.method == "POST":
        sort = request.form['sorted']
        if sort == "New":
            comps = Competitions.query.order_by(Competitions.date_created.desc())
            flash("Competitions now sorted by newest to oldest.")
            return render_template("competitions.html", user=current_user, comps=comps, details=userdetails)
        elif sort == "Top Of Week":
            filter_after = date.today() - timedelta(days = 7)
            comps2 = Competitions.query.filter(Competitions.date_created >= filter_after)
            comps = comps2.order_by(Competitions.submissionnum.desc())
            flash("Competitions now sorted by top of this week.")
            return render_template("competitions.html", user=current_user, comps=comps, details=userdetails)
        elif sort == "Top Of Month":
            filter_after = date.today() - timedelta(days = 30)
            comps2 = Competitions.query.filter(Competitions.date_created >= filter_after)
            comps = comps2.order_by(Competitions.submissionnum.desc())
            flash("Competitions now sorted by top of this month.")
            return render_template("competitions.html", user=current_user, comps=comps, details=userdetails)

    return render_template("competitions.html", user=current_user, comps=comps, details=userdetails)