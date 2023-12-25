# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Screenwriters, Producers, Competitions, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, Notifications, FeaturedScripts
from wtforms import widgets, SelectMultipleField
from werkzeug.utils import secure_filename
import os
import shutil
from werkzeug.utils import secure_filename
import uuid as uuid
from . import db
from datetime import datetime, timedelta, date
import secrets
import PyPDF2
import PyPDF4
from .subroutines import NoSpaces, IsPDF, Watermark, ExtractPDF
from .interact import CreateComment, DeleteComment, LikeExists, RateScreenplay, NotificationExists, ProducerResponse, ProducerRequest, DeletePost
from .update import UpdateNotificationNumber
from .convert import convert_to_datetime, ISOtoDate 
from .load import GiveRecommendations, LoadFeatured

homepage = flask.Blueprint("homepage", __name__)
    
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

@homepage.route("/")
@homepage.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    UpdateNotificationNumber(current_user.id)
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        recs = GiveRecommendations(writer.writerid)
    else:
        recs = None
    sortedposts = Screenplays.query.order_by(Screenplays.avgrating.desc())
    posts = []
    for post in sortedposts:
        if post.date_created == date.today():
            posts.append(post)
    comments = Comments.query.all()
    scripthas = ScriptHas.query.all()
    likes = LikedScreenplays.query.all()
    featured = [None, None, None, None, None, None]
    LoadFeatured(featured, date.today())
    script = featured[0]
    if (script != None) and (datetime.now() >= script.dequeuedatetime): #When the screenplay's time is up, the screenplay is dequeued and removed from the table
        featured.pop()
        feature = FeaturedScripts.query.filter_by(scriptid = script.scriptid).first()
        db.session.delete(feature)
        db.session.commit()
    return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes, script=featured[0], featured=featured)

@homepage.route("/leaderboard", methods=['GET','POST'])
@login_required
def leaderboard():
    UpdateNotificationNumber(current_user.id)
    writers = Screenwriters.query.filter(Screenwriters.experiencelevel > 0).order_by(Screenwriters.experiencelevel)
    return flask.render_template("leaderboard.html", writers=writers, user=current_user)

@homepage.route("/sort", methods=['GET','POST'])
@login_required
def sort():
    UpdateNotificationNumber(current_user.id)
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
    UpdateNotificationNumber(current_user.id)
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
    UpdateNotificationNumber(current_user.id)
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    scripthas = ScriptHas.query.all()
    comments = Comments.query.filter_by(scriptid=scriptid)
    return flask.render_template("script_full.html", post=script, scripthas=scripthas, user=current_user, comments=comments)

@homepage.route("/rate/<scriptid>", methods=['POST'])
@login_required
def rate(scriptid):
    writer = Screenwriters.query.filter_by(userid = current_user.id).first()
    if LikeExists(writer.writerid, scriptid) == False:
        rating = flask.request.form.get("rate")
        RateScreenplay(writer.writerid, scriptid, rating)
        return flask.redirect(flask.url_for('homepage.home'))
    else:
        flask.flash("You've already rated this screenplay!", category="error")
        return flask.redirect(flask.url_for('homepage.home'))

@homepage.route("/create-comment/<scriptid>", methods=['POST'])
@login_required
def create_comment(scriptid):
    text = flask.request.form.get('text')
    if not text:
        flask.flash('Comment cannot be empty.', category='error')
    else:
        CreateComment(scriptid, current_user.id, text)
    return flask.redirect(flask.url_for('homepage.home'))

@homepage.route("/delete-comment/<commentid>", methods=['GET', 'POST'])
@login_required
def delete_comment(commentid):
    DeleteComment(commentid)
    return flask.redirect(flask.url_for('homepage.home'))

@homepage.route('/response/<scriptid>',methods=['POST'])
@login_required
def response(scriptid):
    producer = Producers.query.filter_by(userid = current_user.id).first()
    if NotificationExists(producer.producerid, scriptid, 1) == True:
        flask.flash("You've already sent a response for this script.")
        return flask.redirect(flask.url_for("homepage.home"))
    else:
        response = flask.request.form.get('response')
        ProducerResponse(producer.producerid, scriptid, response)
        return flask.redirect(flask.url_for("homepage.home"))
    
@homepage.route('/request/<scriptid>', methods=['POST'])
@login_required
def request(scriptid):
    producer = Producers.query.filter_by(userid = current_user.id).first()
    if NotificationExists(producer.producerid, scriptid, 2) == True:
        flask.flash("You've already sent a request for this script.")
        return flask.redirect(flask.url_for("homepage.home"))
    else:
        ProducerRequest(producer.producerid, scriptid)
        return flask.redirect(flask.url_for("homepage.home"))

@homepage.route("/delete-post/<scriptid>", methods=['POST'])
@login_required
def delete_post(scriptid):
    DeletePost(scriptid)
    return flask.redirect(flask.url_for('homepage.home'))

@homepage.route("/post", methods=['GET', 'POST'])
@login_required
def post():
    if current_user.accounttype == 1:
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
                                shutil.move(picture_fn,'static/files')
                                PyPDF4.PdfFileReader(scriptname)
                                Watermark(scriptname,"watermarked.pdf", "watermark.pdf")
                                os.remove(scriptname)
                                newname = str(uuid.uuid1()) + "_" + "finalfile.pdf"
                                ExtractPDF(input="watermarked.pdf",output=newname ,start=start, end=end)
                                os.remove("watermarked.pdf")
                                shutil.move(newname,'static/files')
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

    elif current_user.accounttype == 2:
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
    
