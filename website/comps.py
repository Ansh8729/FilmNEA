# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Competitions, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, Notifications, FeaturedScripts
from wtforms import widgets, SelectMultipleField
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

comps = flask.Blueprint("comps", __name__)

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

@comps.route("/competitions", methods=['GET', 'POST'])
@login_required
def competitions():
    comps2 = Competitions.query.all()
    comphas = CompHas.query.all()
    for comp in comps2:
        if datetime.now() > comp.deadline:
            db.session.delete(comp)
            db.session.commit()
        else:
            subs2 = Notifications.query.filter_by(compid = comp.compid)
            comp.submissionnum = subs2.count()
            db.session.commit()
    comps1 = Competitions.query.order_by(Competitions.submissionnum.desc())
    comps = []
    for comp in comps1:
        if comp.date_created == date.today():
            comps.append(comp)
    return flask.render_template("competitions.html", user=current_user, comps=comps, comphas=comphas)

@comps.route("/sort2", methods=['GET','POST'])
@login_required
def sort2():
    comphas = CompHas.query.all()
    sort = flask.request.form.get('sorted')
    if sort == "0":
        return flask.redirect(flask.url_for("comps.competitions"))
    elif sort == "1":
            comps = Competitions.query.order_by(Competitions.date_created.desc())
            flask.flash("Competitions now sorted by newest to oldest.")
            return flask.render_template("competitions.html", user=current_user, comps=comps, comphas=comphas)
    elif sort == "2":
            filter_after = date.today() - timedelta(days = 7)
            comps = Competitions.query.filter(Competitions.datetime_created >= filter_after).order_by(Competitions.submissionnum.desc())
            flask.flash("Competitions now sorted by top of this week.")
            return flask.render_template("competitions.html", user=current_user, comps=comps, comphas=comphas)
    elif sort == "3":
            filter_after = date.today() - timedelta(days = 30)
            comps = Competitions.query.filter(Competitions.datetime_created >= filter_after).order_by(Competitions.submissionnum.desc())
            flask.flash("Competitions now sorted by top of this month.")
            return flask.render_template("competitions.html", user=current_user, comps=comps, comphas=comphas)

@comps.route("/filter2", methods=['GET','POST'])
@login_required
def filter2():
    comphas = CompHas.query.all()
    genre = flask.request.form.get("genre")
    if genre == "0":
        return flask.redirect(flask.url_for("comps.competitions"))
    else:
        genre2 = Genres.query.filter_by(genreid=genre).first()
        compids = CompHas.query.filter_by(genreid=genre).all()
        comps = []
        for i in compids:
            comp = Competitions.query.filter_by(compid=i.compid).first()
            comps.append(comp)
        flask.flash(f"Now showing all {genre2.genre} competitions.")
        return flask.render_template("competitions.html", user=current_user, comps=comps, comphas=comphas)

@comps.route('/comp/<compid>', methods=['GET', 'POST'])
@login_required
def comp(compid):
    comp = Competitions.query.filter_by(compid = compid).first()
    writer = Screenwriters.query.filter_by(userid=current_user.id).first()
    notifs = Notifications.query.filter_by(writerid = writer.writerid)
    submitted = None
    for notif in notifs:
        if notif.compid == compid and submission:
            submitted = True
            break
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
        return flask.redirect(flask.url_for("comps.competitions"))
    return flask.render_template("comp_full.html",user=current_user, comp=comp, submitted=submitted)

@comps.route('/submit/<compid>', methods=['GET', 'POST'])
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
        return flask.redirect(flask.url_for("comps.competitions"))