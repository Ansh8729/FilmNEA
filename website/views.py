# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Competitions, Submissions, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, Responses
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

views = flask.Blueprint("views", __name__)

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
@views.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid = current_user.id).first()
        likedposts = LikedScreenplays.query.filter(LikedScreenplays.rating > 3.5).all()
        scriptids = []
        for i in likedposts:
            if i.writerid == writer.writerid:
                scriptids.append(i.writerid)
        if len(scriptids) == 0:
            recs = []
        else:
            genres = [] 
            for i in range(len(scriptids)):
                info = ScriptHas.query.filter(ScriptHas.scriptid == scriptids[i])
                for j in info:
                    genres.append(j.genreid)
            finalgenres = []
            for i in range(len(genres)):
                genre2 = Genres.query.filter(Genres.genreid == genres[i])
                for j in genre2:
                    finalgenres.append(j.genreid) 
            if list(set(finalgenres)) == finalgenres and len(list(set(finalgenres))) > 1:
                recs = []
            else:
                favgenreid = max(set(finalgenres), key = finalgenres.count)
                query1 = ScriptHas.query.filter(ScriptHas.genreid == favgenreid)
                genreids = []
                for i in query1:
                    genreids.append(i.scriptid)
                likedids = []
                recs = [[],[]]
                query2 = LikedScreenplays.query.all()
                for j in query2:
                    likedids.append(j.scriptid)
                for i in genreids:
                    if i not in likedids: #Only the posts that haven't been liked by the user yet are shown as reccomendations.
                        query3 = Screenplays.query.filter(Screenplays.scriptid == i)
                        for j in query3:
                            recs.append([j.title, j.avgrating])
                            recs.sort()
    posts = Screenplays.query.all()
    comments = Comments.query.all()
    scripthas = ScriptHas.query.all()
    if flask.request.method == "POST":
        sort = flask.request.form.get('sorted')
        if sort == "New":
            posts = Screenplays.query.order_by(Screenplays.scriptid.desc())
            flask.flash("Screenplays now sorted by newest to oldest.")
            return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs)
        elif sort == "Top Of Week":
            filter_after = date.today() - timedelta(days = 7)
            posts2 = Screenplays.query.filter(Screenplays.date_created >= filter_after)
            posts = posts2.order_by(Screenplays.avgrating.desc())
            flask.flash("Screenplays now sorted by top of this week.")
            return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs)
        elif sort == "Top Of Month":
            filter_after = date.today() - timedelta(days = 30)
            posts2 = Screenplays.query.filter(Screenplays.date_created >= filter_after)
            posts = posts2.order_by(Screenplays.avgrating.desc())
            flask.flash("Competitions now sorted by top of this month.")
            return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs)
        genre = flask.request.form.get("genre")
        genre2 = Genres.query.filter_by(genreid=genre).first()
        scriptids = ScriptHas.query.filter_by(genreid=genre).all()
        posts = []
        for i in scriptids:
            script = Screenplays.query.filter_by(scriptid=i.scriptid).first()
            posts.append(script)
        flask.flash(f"Now showing all {genre2.genre} scripts.")
        return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs)
    return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas)

@views.route("/rate/<scriptid>", methods=['POST'])
@login_required
def rate(scriptid):
    rating = flask.request.form.get("rate")
    writer = Screenwriters.query.filter_by(userid = current_user.id).first()
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    newrating = LikedScreenplays(writerid = writer.writerid, scriptid=scriptid, title=script.title, rating=rating)
    db.session.add(newrating)
    db.session.commit()
    ratings = LikedScreenplays.query.filter_by(scriptid = script.scriptid)
    total = 0
    for i in ratings:
        total += i.rating
    script.avgrating = total/ratings.count()
    db.session.commit()
    return flask.redirect(flask.url_for('views.home'))

@views.route("/rate2/<scriptid>", methods=['POST'])
@login_required
def rate2(scriptid):
    rating = flask.request.form.get("rate")
    writer = Screenwriters.query.filter_by(userid = current_user.id).first()
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    newrating = LikedScreenplays(writerid = writer.writerid, scriptid=scriptid, title=script.title, rating=rating)
    db.session.add(newrating)
    db.session.commit()
    ratings = LikedScreenplays.query.filter_by(scriptid = script.scriptid)
    total = 0
    for i in ratings:
        total += i.rating
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    script.avgrating = total/ratings.count()
    db.session.commit()
    return flask.redirect(flask.url_for(f'views.profilepage/{current_user.id}'))

@views.route("/create-comment/<scriptid>", methods=['POST'])
@login_required
def create_comment(scriptid):
    text = flask.request.form.get('text')
    if not text:
        flask.flash('Comment cannot be empty.', category='error')
    else:
        post = Screenplays.query.filter_by(scriptid = scriptid)
        writer = Screenwriters.query.filter_by(userid = current_user.id).first()
        if post:
            comment = Comments(writerid=writer.writerid, scriptid=scriptid, comment=text)
            db.session.add(comment)
            db.session.commit()
        else:
            flask.flash('Post does not exist.', category='error')

    return flask.redirect(flask.url_for('views.home'))

@views.route('/request/<scriptid>',methods=['POST'])
@login_required
def request(scriptid):
    producer = Producers.query.filter_by(userid = current_user.id).first()
    request_exists = Responses.query.filter(Responses.producerid == producer.producerid, Responses.scriptid == scriptid).first()
    if request_exists:
        flask.flash("You've already sent a request for this script.")
    else:
        producer = Producers.query.filter_by(userid = current_user.id).first()
        script = Screenplays.query.filter_by(scriptid=scriptid).first()
        newrequest = Responses(producerid = producer.producerid, writerid=script.writerid, scriptid=scriptid)
        db.session.add(newrequest)
        db.session.commit()
        flask.flash(f"Request for full access for {script.title} sent!")
    return flask.redirect(flask.url_for("views.home"))

@views.route("/delete-post/<scriptid>", methods=['POST'])
@login_required
def delete_post(scriptid):
    if flask.request.method == "POST":
        post = Screenplays.query.filter_by(scriptid = scriptid).first()
        user = Screenwriters.query.filter_by(writerid = post.writerid).first()
        if current_user.id == user.userid:
            comments = Comments.query.filter_by(scriptid = scriptid)
            for i in comments:
                db.session.delete(i)
            ratings = LikedScreenplays.query.filter_by(scriptid = scriptid)
            for i in ratings:
                db.session.delete(i)
            db.session.delete(post)
            db.session.commit()
            flask.flash('Post deleted.', category='success')
            return flask.redirect(flask.url_for('views.home'))

@views.route("/profilepage/<userid>")
@login_required
def profilepage(userid):
    user = Users.query.filter_by(id=userid).first()
    if user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=userid).first()
        scripts = Screenplays.query.filter_by(writerid = writer.writerid)
        rating = 0
        for i in scripts:
            if i.avgrating != None:
                rating += i.avgrating
        writer.experiencelevel = rating*scripts.count()
        db.session.commit()
        writerdetails = Screenwriters.query.filter_by(userid = current_user.id).first()
        comments = Comments.query.all()
        scripthas = ScriptHas.query.all()
        return flask.render_template("profilepage.html", user=current_user, posts=scripts, details=writerdetails, comments=comments, scripthas=scripthas)
    if user.accounttype == 2:
        return flask.render_template("profilepage.html", user=current_user, user2=user)


@views.route("/pageeditor/<username>", methods=['GET', 'POST'])
@login_required
def pageeditor(username):
    if flask.request.method == "POST":
        file = flask.request.files['profilepic']
        picturefilename = secure_filename(file.filename)
        picname = str(uuid.uuid1()) + "_" + picturefilename
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',picname)) 
        shutil.move(picname,'static/images')
        query = Users.query.filter_by(username = username).first()
        query.profilepic = picname
        query.biography = flask.request.form.get('bio')
        db.session.commit()
        if current_user.accounttype == 1:
            colour = flask.request.form.get('colorpicker')
            font = flask.request.form.get('fontstyle')
            writer = Screenwriters.query.filter_by(userid = current_user.id).first()
            writer.backgroundcolour = colour
            if font == 0:
                writer.fontid = None
            else:
                writer.fontstyle = font
            db.session.commit()
        flask.flash("Edits made!")
        writer = Screenwriters.query.filter_by(userid = current_user.id).first()
        scripts = Screenplays.query.filter_by(writerid = writer.writerid)
        comments = Comments.query.all()
        scripthas = ScriptHas.query.all()
        writerdetails = Screenwriters.query.filter_by(userid = current_user.id).first()
        return flask.render_template("profilepage.html", user=current_user, posts=scripts, details=writerdetails, comments=comments, scripthas=scripthas)
    return flask.render_template("pageeditor.html", user=current_user)

@views.route("/post", methods=['GET', 'POST'])
@login_required
def post():
    userdetails = Users.query.filter_by(username = current_user.username).first()
    if userdetails.accounttype == 2:
        if flask.request.method == "POST":
            producerdetails = Producers.query.filter_by(userid = userdetails.id).first()
            num = producerdetails.producerid
            deadline=str(flask.request.form.get("date"))
            date = convert_to_datetime(deadline)
            newcomp = Competitions(producerid = num, title=flask.request.form.get("title"), brief=flask.request.form.get("brief"), deadline=date)
            db.session.add(newcomp)
            db.session.commit()
            newcomp = Competitions.query.order_by(Competitions.compid.desc()).first()
            genres = flask.request.form.getlist("genres")
            for i in genres:
                newcomphas = CompHas(compid=newcomp.compid, genreid=i)
                db.session.add(newcomphas)
                db.session.commit()
            flask.flash("Competition created!")
            return flask.redirect(flask.url_for('views.competitions'))
        return flask.render_template('create_post.html', user=current_user, userdetails=userdetails)
    
    elif userdetails.accounttype == 1:
        if flask.request.method == "POST":
            # The data is grabbed from the form
            title = flask.request.form.get("title")
            logline = flask.request.form.get("logline")
            message = flask.request.form.get("message")
            file = flask.request.files['screenplay']
            start = int(flask.request.form.get("start"))
            end = int(flask.request.form.get("end"))
            genres = flask.request.form.getlist("genres")
            # The file is saved to the folder
            scriptname = secure_filename(file.filename) 
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
            if IsPDF(file.filename) == False:
                flask.flash("Upload a PDF!", category='error')
            else:
                if ValidPageNums(file.filename, start, end) == False:
                    flask.flash("Invalid page range!", category='error')
                else:
                    PyPDF4.PdfFileReader(scriptname)
                    watermark(input_pdf=file.filename,output_pdf="watermarked.pdf", watermark="watermark.pdf")
                    os.remove(file.filename)
                    newname = str(uuid.uuid1()) + "_" + "finalfile.pdf"
                    split_pdf(input="watermarked.pdf",output=newname ,start=start, end=end)
                    os.remove("watermarked.pdf")
                    shutil.move(newname,'static/images')
                    currentwriter = Screenwriters.query.filter_by(userid = current_user.id).first()
                    newpost = Screenplays(writerid = currentwriter.writerid, title=title, logline=logline, message=message, screenplay=newname)
                    db.session.add(newpost)
                    db.session.commit()
                    newscript = Screenplays.query.order_by(Screenplays.scriptid.desc()).first()
                    for i in genres:
                        newscripthas = ScriptHas(scriptid=newscript.scriptid, genreid=i)
                        db.session.add(newscripthas)
                        db.session.commit()
                    posts = Screenplays.query.all()
                    return flask.render_template("home.html", user=current_user, posts=posts)
        return flask.render_template('create_post.html', user=current_user, userdetails=userdetails)

'''
@views.route("/notifications/<userid>", methods=['POST'])
@login_required
def notifications(userid):
    if current_user.accounttype == 1:
        # requests = Requests.query.
    
    if current_user.accounttype == 2:
'''

@views.route("/competitions", methods=['GET', 'POST'])
@login_required
def competitions():
    userdetails = Users.query.filter_by(username = current_user.username).first()
    comps2 = Competitions.query.all()
    subs = Submissions.query.all()
    comphas = CompHas.query.all()
    for comp in comps2:
        subs2 = Submissions.query.filter_by(compid = comp.compid)
        comp.submissionnum = subs2.count()
        db.session.commit()
    comps = Competitions.query.order_by(Competitions.submissionnum.desc())
    if flask.request.method == "POST":
        sort = flask.request.form.get('sorted')
        if sort == "New":
            comps = Competitions.query.order_by(Competitions.date_created.desc())
            flask.flash("Competitions now sorted by newest to oldest.")
            return flask.render_template("competitions.html", user=current_user, comps=comps, details=userdetails, comphas=comphas)
        elif sort == "Top Of Week":
            filter_after = date.today() - timedelta(days = 7)
            comps2 = Competitions.query.filter(Competitions.date_created >= filter_after)
            comps = comps2.order_by(Competitions.submissionnum.desc())
            flask.flash("Competitions now sorted by top of this week.")
            return flask.render_template("competitions.html", user=current_user, comps=comps, details=userdetails, comphas=comphas)
        elif sort == "Top Of Month":
            filter_after = date.today() - timedelta(days = 30)
            comps2 = Competitions.query.filter(Competitions.date_created >= filter_after)
            comps = comps2.order_by(Competitions.submissionnum.desc())
            flask.flash("Competitions now sorted by top of this month.")
            return flask.render_template("competitions.html", user=current_user, comps=comps, details=userdetails, comphas=comphas)
        genre = flask.request.form.get("genre")
        genre2 = Genres.query.filter_by(genreid=genre).first()
        compids = CompHas.query.filter_by(genreid=genre).all()
        comps = []
        for i in compids:
            comp = Competitions.query.filter_by(compid=i.compid).first()
            comps.append(comp)
        flask.flash(f"Now showing all {genre2.genre} competitions.")

    return flask.render_template("competitions.html", user=current_user, comps=comps, details=userdetails, comphas=comphas)

@views.route('/comp/<title>', methods=['GET', 'POST'])
@login_required
def comp(title):
    comp = Competitions.query.filter_by(title = title).first()
    if flask.request.method == "POST":
        submission = flask.request.files["submissions"]
        scriptname = secure_filename(submission.filename) 
        submission.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
        user = Users.query.filter_by(username = current_user.username).first()
        writer = Screenwriters.query.filter_by(userid = user.id).first()
        newsub = Submissions(writerid = writer.writerid, compid = comp.compid, submission=scriptname)
        db.session.add(newsub)
        db.session.commit()
        flask.flash("Submission sent!")
        return flask.redirect(flask.url_for("views.competitions"))
    return flask.render_template("comp_full.html",user=current_user, comp=comp)

@views.route('/notifications/<userid>')
@login_required
def notifications(userid):
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=userid).first()
        responses = Responses.query.filter_by(writerid = writer.writerid)
        '''
        if flask.request.method == "POST":
            decision = flask.request.form.get("decision")
            if decision == "Accept":
                
            if decision == "Decline":
        '''
        
    return flask.render_template("notifications.html", requests=responses, user=current_user)

