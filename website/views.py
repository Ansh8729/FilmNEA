# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Competitions, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, Notifications
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
import secrets

views = flask.Blueprint("views", __name__)

def convert_to_datetime(input_str, parserinfo=None):
    return parse(input_str, parserinfo=parserinfo)
    
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
        flask.flash("Your filename CANNOT have spaces!")
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

def GiveReccomendations(id):
    writer = Screenwriters.query.filter_by(userid = id).first()
    likedposts = LikedScreenplays.query.filter(LikedScreenplays.rating > 3.5).all()
    scriptids = []
    for i in likedposts:
        if i.writerid == writer.writerid:
            scriptids.append(i.writerid)
    if len(scriptids) == 0:
        return []
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
            return []
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
            return recs

@views.route("/")
@views.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    if current_user.accounttype == 1:
        recs = GiveReccomendations(current_user.id)
    posts = Screenplays.query.all()
    comments = Comments.query.all()
    scripthas = ScriptHas.query.all()
    if flask.request.method == "POST":
        sort = flask.request.form.get('sorted')
        if sort == "New":
            posts = Screenplays.query.order_by(Screenplays.scriptid.desc())
            flask.flash("Screenplays now sorted by newest to oldest.")
            return flask.redirect(flask.url_for("views.home"))
        elif sort == "Top Of Week":
            filter_after = date.today() - timedelta(days = 7)
            posts2 = Screenplays.query.filter(Screenplays.date_created >= filter_after)
            posts = posts2.order_by(Screenplays.avgrating.desc())
            flask.flash("Screenplays now sorted by top of this week.")
            return flask.redirect(flask.url_for("views.home"))
        elif sort == "Top Of Month":
            filter_after = date.today() - timedelta(days = 30)
            posts2 = Screenplays.query.filter(Screenplays.date_created >= filter_after)
            posts = posts2.order_by(Screenplays.avgrating.desc())
            flask.flash("Competitions now sorted by top of this month.")
            return flask.redirect(flask.url_for("views.home"))
        genre = flask.request.form.get("genre")
        genre2 = Genres.query.filter_by(genreid=genre).first()
        scriptids = ScriptHas.query.filter_by(genreid=genre).all()
        posts = []
        for i in scriptids:
            script = Screenplays.query.filter_by(scriptid=i.scriptid).first()
            posts.append(script)
        flask.flash(f"Now showing all {genre2.genre} scripts.")
        return flask.redirect(flask.url_for("views.home"))
    return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs)

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
        post = Screenplays.query.filter_by(scriptid = scriptid).first()
        writer = Screenwriters.query.filter_by(userid = current_user.id).first()
        if post:
            comment = Comments(writerid=writer.writerid, scriptid=scriptid, comment=text)
            db.session.add(comment)
            db.session.commit()
            comment = Comments.query.order_by(Comments.commentid).first()
            writer = Screenwriters.query.filter_by(userid = current_user.id).first()
            notif = Notifications(writerid = writer.writerid, commentid=comment.commentid)
            db.session.add(notif)
            db.session.commit()
        else:
            flask.flash('Post does not exist.', category='error')

    return flask.redirect(flask.url_for('views.home'))

@views.route("/delete-comment/<commentid>", methods=['GET', 'POST'])
@login_required
def delete_comment(commentid):
    notif = Notifications.query.filter_by(commentid=commentid).first()
    if notif:
        db.session.delete(notif)
        db.session.commit()
    comment = Comments.query.filter_by(commentid=commentid).first()
    db.session.delete(comment)
    db.session.commit()
    flask.flash("Comment removed!")
    return flask.redirect(flask.url_for('views.home'))
    

@views.route('/response/<scriptid>',methods=['POST'])
@login_required
def response(scriptid):
    response = flask.request.form.get('response')
    request = flask.request.form.get('request')
    if response:
        producer = Producers.query.filter_by(userid = current_user.id).first()
        response_exists = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.scriptid == scriptid, Notifications.responsetype == 1).first()
        if response_exists:
            flask.flash("You've already sent a response for this script.")
            return flask.redirect(flask.url_for("views.home"))
        else:
            producer = Producers.query.filter_by(userid = current_user.id).first()
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            newresponse = Notifications(producerid = producer.producerid, writerid=script.writerid, scriptid=scriptid, message=response, responsetype = 1)
            db.session.add(newresponse)
            db.session.commit()
            flask.flash(f"Response sent!")
        return flask.redirect(flask.url_for("views.home"))
    elif request:
        producer = Producers.query.filter_by(userid = current_user.id).first()
        request_exists = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.scriptid == scriptid, Notifications.responsetype == 2).first()
        if request_exists:
            flask.flash("You've already sent a request for this script.")
            return flask.redirect(flask.url_for("views.home"))
        else:
            producer = Producers.query.filter_by(userid = current_user.id).first()
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            newrequest = Notifications(producerid = producer.producerid, writerid=script.writerid, scriptid=scriptid, responsetype = 2, requeststatus = 0)
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
    profileuser = Users.query.filter_by(id=userid).first()
    if profileuser.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=userid).first()
        scripts = Screenplays.query.filter_by(writerid = writer.writerid)
        rating = 0
        for i in scripts:
            if i.avgrating != None:
                rating += i.avgrating
        writer.experiencelevel = rating*scripts.count()
        db.session.commit()
        comments = Comments.query.all()
        scripthas = ScriptHas.query.all()
        return flask.render_template("profilepage.html", user=current_user, posts=scripts, comments=comments, scripthas=scripthas, profileuser=profileuser, details=writer)
    if profileuser.accounttype == 2:
        return flask.render_template("profilepage.html", user=current_user, profileuser=profileuser)


@views.route("/pageeditor/<userid>", methods=['GET', 'POST'])
@login_required
def pageeditor(userid):
    if flask.request.method == "POST":
        file = flask.request.files['profilepic']
        picturefilename = secure_filename(file.filename)
        picname = str(uuid.uuid1()) + "_" + picturefilename
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',picname)) 
        shutil.move(picname,'static/images')
        profile = Users.query.filter_by(id = userid).first()
        profile.profilepic = picname
        profile.biography = flask.request.form.get('bio')
        db.session.commit()
        if current_user.accounttype == 1:
            colour = flask.request.form.get('colorpicker')
            font = flask.request.form.get('fontstyle')
            writer = Screenwriters.query.filter_by(userid = userid).first()
            writer.backgroundcolour = colour
            if font == 0:
                writer.fontid = None
            else:
                writer.fontstyle = font
            db.session.commit()
        flask.flash("Edits made!")
        return flask.redirect(flask.url_for('views.profilepage', userid=current_user.id))
    
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
            if IsPDF(scriptname) == False:
                flask.flash("Upload a PDF!", category='error')
                os.remove(scriptname)
            else:
                file2 = PyPDF2.PdfReader(scriptname)
                nums = len(file2.pages)
                if end > nums:
                    flask.flash("Your screenplay doesn't have "+str(end)+" pages!")
                    os.remove(scriptname)
                elif end-start > 10:
                    flask.flash("You can't upload more than 10 pages!")
                    os.remove(scriptname)
                else:
                    random_hex = secrets.token_hex(8)
                    _, f_ext = os.path.splitext(scriptname)
                    picture_fn = random_hex + f_ext
                    shutil.copyfile(scriptname, picture_fn)
                    shutil.move(picture_fn,'static/images')
                    PyPDF4.PdfFileReader(scriptname)
                    watermark(input_pdf=file.filename,output_pdf="watermarked.pdf", watermark="watermark.pdf")
                    os.remove(file.filename)
                    newname = str(uuid.uuid1()) + "_" + "finalfile.pdf"
                    split_pdf(input="watermarked.pdf",output=newname ,start=start, end=end)
                    os.remove("watermarked.pdf")
                    shutil.move(newname,'static/images')
                    currentwriter = Screenwriters.query.filter_by(userid = current_user.id).first()
                    newpost = Screenplays(writerid = currentwriter.writerid, title=title, logline=logline, message=message, screenplay=newname, fullfile=picture_fn)
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

@views.route("/competitions", methods=['GET', 'POST'])
@login_required
def competitions():
    userdetails = Users.query.filter_by(username = current_user.username).first()
    comps2 = Competitions.query.all()
    comphas = CompHas.query.all()
    for comp in comps2:
        subs2 = Notifications.query.filter_by(compid = comp.compid)
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

@views.route('/comp/<compid>', methods=['GET', 'POST'])
@login_required
def comp(compid):
    comp = Competitions.query.filter_by(compid = compid).first()
    if flask.request.method == "POST":
        submission = flask.request.files["submissions"]
        scriptname = secure_filename(submission.filename) 
        submission.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
        user = Users.query.filter_by(username = current_user.username).first()
        writer = Screenwriters.query.filter_by(userid = user.id).first()
        newsub = Notifications(writerid = writer.writerid, compid = comp.compid, submission=scriptname)
        db.session.add(newsub)
        db.session.commit()
        flask.flash("Submission sent!")
        return flask.redirect(flask.url_for("views.competitions"))
    return flask.render_template("comp_full.html",user=current_user, comp=comp)

@views.route('/submit/<compid>', methods=['GET', 'POST'])
@login_required
def submit(compid):
    file = flask.request.files['submission']
    scriptname = secure_filename(file.filename) 
    file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
    shutil.move(scriptname,'static/images')
    if IsPDF(file.filename) == False:
        flask.flash("Upload a PDF!", category='error')
    else:
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        comp = Competitions.query.filter_by(compid=compid).first()
        newsub = Notifications(writerid=writer.writerid, producerid=comp.producerid, compid=compid, submission=file.filename)
        db.session.add(newsub)
        db.session.commit()
        flask.flash("Submission sent!")
        return flask.redirect(flask.url_for("views.competitions"))
    
@views.route('/notifications/<userid>', methods=['GET', 'POST'])
@login_required
def notifications(userid):
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=userid).first()
        notifs = Notifications.query.filter_by(writerid = writer.writerid)
    if current_user.accounttype == 2:
        producer = Producers.query.filter_by(userid=userid).first()
        notifs = Notifications.query.filter_by(producerid = producer.producerid)

    return flask.render_template("notifications.html", notifs=notifs, user=current_user)
    
@views.route('/sendback/<userid>/<compid>', methods=['GET', 'POST'])
@login_required
def sendback(userid, compid):
    if current_user.accounttype == 2:
        response = flask.request.form.get('subresponse')
        producer = Producers.query.filter_by(userid=current_user.id).first()
        writer = Screenwriters.query.filter_by(userid=userid).first()  
        sub = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.writerid==writer.writerid, Notifications.compid == compid).first()
        message = f"{producer.user.username} responded to your submission to their competition {sub.comp.title}: {response}"
        sub.message = message
        db.session.commit()
        flask.flash("Response sent!")
        return flask.redirect(flask.url_for("views.notifications", userid=current_user.id))
        
@views.route('/deleteresponse/<responseid>', methods=['GET', 'POST'])
@login_required
def deleteresponse(responseid):
    response = Notifications.query.filter_by(notifid = responseid).first()
    db.session.delete(response)
    db.session.commit()
    flask.flash("Response removed!")
    return flask.redirect(flask.url_for("views.notifications", userid=current_user.id))

@views.route('/requestresponse/<requestid>', methods=['GET', 'POST'])
@login_required
def requestresponse(requestid):
    decision = flask.request.form.get('decision')
    request = Notifications.query.filter_by(notifid=requestid).first()
    if decision == "Accept":
        request.requeststatus = 1
        request.message = f"{request.writer.user.username} has accepted your request for full access to {request.script.title}! Here's a link to the full file."
        db.session.commit()
        flask.flash("Request accepted!")
    elif decision == "Decline":
        request.requeststatus = 2
        request.message = f"{request.writer.user.username} has declined your request for full access to {request.script.title}!"
        db.session.commit()
        flask.flash("Request declined!")
    return flask.redirect(flask.url_for("views.notifications", userid=current_user.id))

    

    


    

    
    

