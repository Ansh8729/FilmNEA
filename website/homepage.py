# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Competitions, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, Notifications, FeaturedScripts
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
from datetime import datetime, timedelta, date
import secrets

homepage = flask.Blueprint("homepage", __name__)

def convert_to_datetime(input_str, parserinfo=None):
    return parse(input_str, parserinfo=parserinfo)
    
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

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

def GiveRecommendations(writerid):
    posts = LikedScreenplays.query.filter(LikedScreenplays.rating > 3.5).all()
    postids = [] 
    for i in posts:
        if i.writerid == writerid:
            postids.append(i.scriptid) #The ScriptIDs of the posts the user has rated above 3.5 are stored in a list.

    if len(postids) == 0: #Validates if the query returned any data
        recs = None
        return recs
    else:
        genres = [] 
        for i in range(len(postids)):
            info = ScriptHas.query.filter(ScriptHas.scriptid == postids[i])
            for j in info:
                genres.append(j.genreid) #The GenreIDs of the liked posts are found

        finalgenres = []
        for i in range(len(genres)):
            genre2 = Genres.query.filter(Genres.genreid == genres[i])
            for j in genre2:
                finalgenres.append(j.genreid) 
        if (list(set(finalgenres)) == finalgenres and len(list(set(finalgenres))) > 1) or len(finalgenres) == 0:
            recs = None
            return recs
        else:
            favgenreid = max(set(finalgenres), key = finalgenres.count) #The GenreIDs are used to find the liked genre and then the user's most liked genre
            #If the user doesn't have a particular favourite, nothing is reccomended 

        query1 = ScriptHas.query.filter(ScriptHas.genreid == favgenreid)
        genreids = []
        for i in query1:
            genreids.append(i.scriptid) #The ScriptIDs whose posts are of the user's favourite genre are found
        
        likedids = []
        recs = []
        query2 = LikedScreenplays.query.all()
        for j in query2:
            likedids.append(j.scriptid)
        for i in genreids:
            if (i not in likedids): #Only the posts that haven't been liked by the user yet are shown as reccomendations.
                query3 = Screenplays.query.filter(Screenplays.scriptid == i).first()
                if query3.writer.user.id != current_user.id:
                    recs.append(query3)
        return recs

class Queue: #Code for the queue that is fundamental to this feature

    def __init__(self, mymax):
        self.mymax = mymax
        self.queue = [None] * self.mymax
        self.head = 0
        self.tail = -1
        
    def isFull(self):
        if self.tail + 1 == self.mymax:
            return True 
        else:
            return False

    def isEmpty(self):
        if self.head > self.tail:
            return True
        else:
            return False

    def enqueue(self, num):
        if self.isFull() == False:
            self.tail += 1
            self.queue[self.tail] = num
    
    def dequeue(self):
        if self.isEmpty() == False:
            self.queue[self.head] = None
            self.head += 1

def FeaturedExists(scriptid): #This function prevents duplicates from being enqueued
    query = FeaturedScripts.query.filter_by(scriptid = scriptid).first()
    if query:
        return True
    else:
        return False

def LoadFeatured(queue, date): 
    posts = Screenplays.query.filter_by(date_created = date) #Posts from today selected
    hour = 4
    for post in posts:
        likes = LikedScreenplays.query.filter(LikedScreenplays.scriptid == post.scriptid, LikedScreenplays.rating >= 4.0)
        if likes.count() >= 3 and FeaturedExists(post.scriptid) == False: #The screenplay is checked if it qualifies to be featured
            newfeatured = FeaturedScripts(scriptid = post.scriptid, dequeuedatetime = datetime.now()+timedelta(hours=hour))
            db.session.add(newfeatured)
            db.session.commit()
            hour += 4
    scripts = FeaturedScripts.query.filter(FeaturedScripts.featuredid <= 5) #The first 6 records are enqueued from the database to the queue
    for i in scripts:
        queue.enqueue(i)

def ISOtoDate(date):
    months = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04":"April",
    "05":"May",
    "06":"June",
    "07":"July",
    "08":"August",
    "09":"September",
    "10":"October",
    "11":"November",
    "12":"December"}
    datestr = str(datetime.fromisoformat(date))
    date2 = list(datestr)[0:10]
    daynum = ''.join(date2[8]+date2[9])
    if date2[9] == "1":
        day = daynum+"st"
    elif daynum == "02" or daynum == "22":
        day = daynum+"st"
    elif daynum == "03" or daynum == "23":
        day = daynum+"rd"
    else:
        day = daynum +"th"
    if day[0] == "0":
        day = list(day)
        day = day[1:6]
        day = ''.join(day)
    month = months[''.join(date2[5]+date2[6])]
    year = ''.join(date2[0:4])
    return f"{day} {month} {year}"

@homepage.route("/")
@homepage.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        recs = GiveRecommendations(writer.writerid)
    else:
        recs = None
    posts1 = Screenplays.query.order_by(Screenplays.avgrating.desc())
    posts = []
    for i in posts1:
        if i.date_created == date.today():
            posts.append(i)
    comments = Comments.query.all()
    scripthas = ScriptHas.query.all()
    likes = LikedScreenplays.query.all()
    featured = Queue(5)
    LoadFeatured(featured, date.today())
    script = featured.queue[featured.head]
    if (script != None) and (datetime.now() >= script.dequeuedatetime): #When the screenplay's time is up, the screenplay is dequeued and removed from the table
        featured.dequeue()
        feature = FeaturedScripts.query.filter_by(scriptid = script.scriptid).first()
        db.session.delete(feature)
        db.session.commit()
    return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes, script=featured.queue[featured.head], featured=featured)

@homepage.route("/leaderboard", methods=['GET','POST'])
@login_required
def leaderboard():
    writers = Screenwriters.query.order_by(Screenwriters.experiencelevel)
    return flask.render_template("leaderboard.html", writers=writers, user=current_user)

@homepage.route("/sort", methods=['GET','POST'])
@login_required
def sort():
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        recs = GiveRecommendations(writer.writerid)
    posts = Screenplays.query.all()
    comments = Comments.query.all()
    scripthas = ScriptHas.query.all()
    likes = LikedScreenplays.query.all()
    sort = flask.request.form.get('sorted')
    if sort == "0":
        return flask.redirect(flask.url_for("homepage.home"))
    elif sort == "1":
            posts = Screenplays.query.order_by(Screenplays.scriptid.desc())
            flask.flash("Screenplays now sorted by newest to oldest.")
            return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes)
    elif sort == "2":
            filter_after = datetime.now() - timedelta(days = 7)
            posts1 = Screenplays.query.order_by(Screenplays.avgrating.desc())
            posts = []
            for i in posts1:
                if i.datetime_created >= filter_after:
                    posts.append(i)
            flask.flash("Screenplays now sorted by top of this week.")
            return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes)
    elif sort == "3":
            filter_after = datetime.now() - timedelta(days = 30)
            posts1 = Screenplays.query.order_by(Screenplays.avgrating.desc())
            posts = []
            for i in posts1:
                if i.datetime_created >= filter_after:
                    posts.append(i)
            flask.flash("Screenplays now sorted by top of this month.")
            return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes)

@homepage.route("/filter", methods=['GET','POST'])
@login_required
def filter():
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        recs = GiveRecommendations(writer.writerid)
    else:
        recs = None
    posts = Screenplays.query.all()
    comments = Comments.query.all()
    scripthas = ScriptHas.query.all()
    likes = LikedScreenplays.query.all()
    genre = flask.request.form.get("genre")
    if genre == "0":
        return flask.redirect(flask.url_for("homepage.home"))
    else:
        genre2 = Genres.query.filter_by(genreid=genre).first()
        scriptids = ScriptHas.query.filter_by(genreid=genre).all()
        posts = []
        for i in scriptids:
            script = Screenplays.query.filter_by(scriptid=i.scriptid).first()
            posts.append(script)
        flask.flash(f"Now showing all {genre2.genre} scripts.")
        return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes)

@homepage.route("/script/<scriptid>", methods=['GET', 'POST'])
@login_required
def script(scriptid):
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    scripthas = ScriptHas.query.all()
    comments = Comments.query.filter_by(scriptid=scriptid)
    return flask.render_template("script_full.html", post=script, scripthas=scripthas, user=current_user, comments=comments)

@homepage.route("/rate/<scriptid>", methods=['POST'])
@login_required
def rate(scriptid):
    rating = flask.request.form.get("rate")
    writer = Screenwriters.query.filter_by(userid = current_user.id).first()
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    like_exists = LikedScreenplays.query.filter(LikedScreenplays.writerid == writer.writerid, LikedScreenplays.scriptid==scriptid).first()
    if not like_exists:
        newrating = LikedScreenplays(writerid = writer.writerid, scriptid=scriptid, rating=rating)
        db.session.add(newrating)
        db.session.commit()
    else:
        flask.flash("You've already rated this screenplay!", category="error")
        return flask.redirect(flask.url_for('homepage.home'))
    ratings = LikedScreenplays.query.filter_by(scriptid = scriptid)
    total = 0
    for i in ratings:
        total += i.rating
    script.avgrating = total/ratings.count()
    db.session.commit()
    flask.flash("Rating submitted!")
    return flask.redirect(flask.url_for('homepage.home'))

@homepage.route("/create-comment/<scriptid>", methods=['POST'])
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
            writer2 = Screenwriters.query.filter_by(userid = post.writer.user.id).first()
            notif = Notifications(writerid = writer2.writerid, responsetype = 3, commentid=comment.commentid)
            db.session.add(notif)
            db.session.commit()
        else:
            flask.flash('Post does not exist.', category='error')

    return flask.redirect(flask.url_for('homepage.home'))

@homepage.route("/delete-comment/<commentid>", methods=['GET', 'POST'])
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
    return flask.redirect(flask.url_for('homepage.home'))

@homepage.route('/response/<scriptid>',methods=['POST'])
@login_required
def response(scriptid):
    response = flask.request.form.get('response')
    request = flask.request.form.get('request')
    if response:
        producer = Producers.query.filter_by(userid = current_user.id).first()
        response_exists = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.scriptid == scriptid, Notifications.responsetype == 1).first()
        if response_exists:
            flask.flash("You've already sent a response for this script.")
            return flask.redirect(flask.url_for("homepage.home"))
        else:
            producer = Producers.query.filter_by(userid = current_user.id).first()
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            newresponse = Notifications(producerid = producer.producerid, writerid=script.writerid, scriptid=scriptid, message=response, responsetype = 1)
            db.session.add(newresponse)
            db.session.commit()
            flask.flash(f"Response sent!")
        return flask.redirect(flask.url_for("homepage.home"))
    elif request:
        producer = Producers.query.filter_by(userid = current_user.id).first()
        request_exists = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.scriptid == scriptid, Notifications.responsetype == 2).first()
        if request_exists:
            flask.flash("You've already sent a request for this script.")
            return flask.redirect(flask.url_for("homepage.home"))
        else:
            producer = Producers.query.filter_by(userid = current_user.id).first()
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            newrequest = Notifications(producerid = producer.producerid, writerid=script.writerid, scriptid=scriptid, responsetype = 2, requeststatus = 0)
            db.session.add(newrequest)
            db.session.commit()
            flask.flash(f"Request for full access for {script.title} sent!")
        return flask.redirect(flask.url_for("homepage.home"))

@homepage.route("/delete-post/<scriptid>", methods=['POST'])
@login_required
def delete_post(scriptid):
        post = Screenplays.query.filter_by(scriptid = scriptid).first()
        scripthas = ScriptHas.query.all()
        for record in scripthas:
            if record.scriptid == post.scriptid:
                db.session.delete(record)
                db.session.commit()
        comments = Comments.query.filter_by(scriptid = post.scriptid)
        for comment in comments:
            db.session.delete(comment)
            db.session.commit()
        ratings = LikedScreenplays.query.filter_by(scriptid = post.scriptid)
        for i in ratings:
            db.session.delete(i)
            db.session.commit()
        notifs = LikedScreenplays.query.filter_by(scriptid = post.scriptid)
        for i in notifs:
            db.session.delete(i)
            db.session.commit()
        post = Screenplays.query.filter_by(scriptid = scriptid).first()
        db.session.delete(post)
        db.session.commit()
        flask.flash('Post deleted.', category='success')
        return flask.redirect(flask.url_for('homepage.home'))

@homepage.route("/post", methods=['GET', 'POST'])
@login_required
def post():
    if current_user.accounttype == 2:
        if flask.request.method == "POST":
            producerdetails = Producers.query.filter_by(userid = current_user.id).first()
            num = producerdetails.producerid
            deadline = str(flask.request.form.get("date"))
            date = convert_to_datetime(deadline)
            if date < datetime.today():
                flask.flash("Invalid deadline. Set a deadline today or after today.", category="error")
                return flask.redirect(flask.url_for("homepage.post"))
            else:
                title = flask.request.form.get("title")
                title_exists = Competitions.query.filter_by(title=title).first()
                if title_exists:
                    flask.flash("Title is already being used.", category="error")
                    return flask.redirect(flask.url_for("homepage.post"))
                else:
                    newcomp = Competitions(producerid = num, title=flask.request.form.get("title"), brief=flask.request.form.get("brief"), deadline=date, deadline_string=ISOtoDate(deadline))
                    db.session.add(newcomp)
                    db.session.commit()
                    newcomp = Competitions.query.order_by(Competitions.compid.desc()).first()
                    genres = flask.request.form.getlist("genres")
                    for i in genres:
                        newcomphas = CompHas(compid=newcomp.compid, genreid=i)
                        db.session.add(newcomphas)
                        db.session.commit()
                    flask.flash("Competition created!")
                    return flask.redirect(flask.url_for('comps.competitions'))
        return flask.render_template('create_post.html', user=current_user)
    
    elif current_user.accounttype == 1:
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
            title_exists = Screenplays.query.filter_by(title=title).first()
            if title_exists:
                flask.flash("Title is already being used.", category="error")
                flask.redirect(flask.url_for("homepage.post"))
            else:
                if len(logline) > 165:
                    flask.flash("Logline is too long!", category="error")
                    flask.redirect(flask.url_for("homepage.post"))
                else:
                    if len(message) > 280:
                        flask.flash("Message is too long!", category="error")
                        flask.redirect(flask.url_for("homepage.post"))
                    else:
                        scriptname = secure_filename(file.filename)
                        scriptname = NoSpaces(scriptname)
                        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
                        if IsPDF(scriptname) == False:
                            flask.flash("Upload a PDF!", category='error')
                            os.remove(scriptname)
                            return flask.redirect(flask.url_for("homepage.post"))
                        else:
                            file2 = PyPDF2.PdfReader(scriptname)
                            nums = len(file2.pages)
                            if end > nums:
                                flask.flash("Your screenplay doesn't have "+str(end)+" pages!")
                                os.remove(scriptname)
                                return flask.redirect(flask.url_for("homepage.post"))
                            elif end-start > 10:
                                flask.flash("You can't upload more than 10 pages!")
                                os.remove(scriptname)
                                return flask.redirect(flask.url_for("homepage.post"))
                            else:
                                random_hex = secrets.token_hex(8)
                                _, f_ext = os.path.splitext(scriptname)
                                picture_fn = random_hex + f_ext
                                shutil.copyfile(scriptname, picture_fn)
                                shutil.move(picture_fn,'static/images')
                                PyPDF4.PdfFileReader(scriptname)
                                watermark(input_pdf=scriptname,output_pdf="watermarked.pdf", watermark="watermark.pdf")
                                os.remove(scriptname)
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
                                return flask.redirect(flask.url_for("homepage.home"))
        return flask.render_template('create_post.html', user=current_user)