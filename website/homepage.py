import flask 
from flask_login import login_required, current_user
from .models import Screenwriters, Producers, Competitions, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, FeaturedScripts
from werkzeug.utils import secure_filename
import os
import shutil
import uuid as uuid
from . import db
from datetime import datetime, timedelta, date
import secrets
import PyPDF2
import PyPDF4
from .subroutines import NoSpaces
from .pdf import IsPDF, Watermark, ExtractPDF
from .interact import CreateComment, DeleteComment, LikeExists, RateScreenplay, NotificationExists, ProducerResponse, ProducerRequest, DeletePost
from .update import UpdateNotificationNumber, UpdateExperienceLevel
from .convert import convert_to_datetime, ISOtoDate 
from .load import GiveRecommendations, LoadFeatured

homepage = flask.Blueprint("homepage", __name__)

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

    posts = Screenplays.query.filter_by(date_created = date.today()).order_by(Screenplays.avgrating.desc())
    comments = Comments.query.all()
    scripthas = ScriptHas.query.all()
    likes = LikedScreenplays.query.all()
    featured = [None, None, None, None, None, None]
    LoadFeatured(featured, date.today())
    script = featured[0]

    #When the screenplay's time is up, the screenplay is dequeued and removed from the table
    if (script != None) and (datetime.now() >= script.dequeuedatetime): 
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
    leaderboard = []
    number = 1
    for writer in writers:
        leaderboard.append([number, writer])
        number += 1

    return flask.render_template("leaderboard.html", writers=leaderboard, user=current_user)

@homepage.route("/sort", methods=['GET','POST'])
@login_required
def sort():
    UpdateNotificationNumber(current_user.id)
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        recs = GiveRecommendations(writer.writerid)
    else:
        recs == None 

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
            filter_after = date.today() - timedelta(days = 7)
            posts = Screenplays.query.filter(Screenplays.datetime_created >= filter_after).order_by(Screenplays.avgrating.desc())
            flask.flash("Screenplays now sorted by top of this week.")
            return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes)
    elif sort == "3":
            filter_after = date.today() - timedelta(days = 30)
            posts = Screenplays.query.filter(Screenplays.datetime_created >= filter_after).order_by(Screenplays.avgrating.desc())
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
        for script in scriptids:
            script = Screenplays.query.filter_by(scriptid=script.scriptid).first()
            posts.append(script)
        flask.flash(f"Now showing all {genre2.genre} scripts.")
        return flask.render_template("home.html", user=current_user, posts=posts, comments=comments, scripthas=scripthas, recs=recs, likes=likes)

@homepage.route("/rate/<scriptid>", methods=['POST'])
@login_required
def rate(scriptid):
    writer = Screenwriters.query.filter_by(userid = current_user.id).first()
    if LikeExists(writer.writerid, scriptid) == False:
        rating = flask.request.form.get("rate")
        RateScreenplay(writer.writerid, scriptid, rating)
        UpdateExperienceLevel(writer.user.id)
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
    if flask.request.method == "POST":
        if current_user.accounttype == 1:
            try: 
                # Data is fetched
                title = flask.request.form.get("title")
                logline = flask.request.form.get("logline")
                message = flask.request.form.get("message")
                file = flask.request.files['screenplay']
                start = int(flask.request.form.get("start"))
                end = int(flask.request.form.get("end"))
                genres = flask.request.form.getlist("genres")
                scriptname = secure_filename(file.filename)
                scriptname = NoSpaces(scriptname)
                file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
                file2 = PyPDF2.PdfReader(scriptname)
                num_of_pages = len(file2.pages)
                title_exists = Screenplays.query.filter_by(title=title).first()

                # Exceptions are handled 
                if title_exists:
                    raise ValueError("Title is already being used.")
                elif len(logline) > 165:
                    raise ValueError("Logline is too long!")
                elif len(message) > 280:
                    raise ValueError("Message is too long!")
                elif not genres:
                    raise ValueError("Tag your post with at least one genre.")
                elif IsPDF(scriptname) == False:
                    os.remove(scriptname)
                    raise ValueError("Upload a PDF!")
                elif end > num_of_pages:
                    os.remove(scriptname)
                    raise ValueError("Your screenplay doesn't have "+str(end)+" pages!")
                elif (end-start) > 9:
                    os.remove(scriptname)
                    raise ValueError("You can't upload more than 10 pages!")
                elif (end == start) or (start > end):
                    os.remove(scriptname)
                    raise ValueError("Invalid page numbers!")
                
                # Full screenplay saved
                random_hex = secrets.token_hex(8)
                _, f_ext = os.path.splitext(scriptname)
                fullfilename = random_hex + f_ext
                shutil.copyfile(scriptname, fullfilename)
                shutil.move(fullfilename,'static/files')

                # File to be posted is watermarked and chosen range of pages are extracted
                PyPDF4.PdfFileReader(scriptname)
                Watermark(scriptname,"watermarked.pdf", "watermark.pdf")
                os.remove(scriptname)
                newname = str(uuid.uuid1()) + "_" + "finalfile.pdf"
                ExtractPDF(input="watermarked.pdf",output=newname ,start=start, end=end)
                os.remove("watermarked.pdf")
                shutil.move(newname,'static/files')

                # Post is created
                currentwriter = Screenwriters.query.filter_by(userid = current_user.id).first()
                newpost = Screenplays(writerid = currentwriter.writerid, title=title, logline=logline, message=message, screenplay=newname, fullfile=fullfilename)
                db.session.add(newpost)
                db.session.commit()

                # Genre tags are added
                newscript = Screenplays.query.order_by(Screenplays.scriptid.desc()).first()
                for genre in genres:
                    newscripthas = ScriptHas(scriptid=newscript.scriptid, genreid=genre)
                    db.session.add(newscripthas)
                    db.session.commit()
                return flask.redirect(flask.url_for("homepage.home"))                                           

            except ValueError as e:
                flask.flash(str(e), category='error')
                flask.redirect(flask.url_for("homepage.post"))
                                    
            return flask.render_template('create_post.html', user=current_user)

        elif current_user.accounttype == 2:
            try: 
                # Data is fetched
                title = flask.request.form.get("title")
                brief = flask.request.form.get("brief")
                genres = flask.request.form.getlist("genres")
                deadline = str(flask.request.form.get("date"))
                date = convert_to_datetime(deadline)
                title_exists = Competitions.query.filter_by(title=title).first()

                # Exceptions are handled 
                if date <= datetime.today():
                    raise ValueError("Invalid deadline. Set a deadline for after today.")
                elif title_exists:
                    raise ValueError("Title is already being used.")
                elif not genres:
                    raise ValueError("Tag your competition with at least one genre.")
                
                # Competition is created
                producerdetails = Producers.query.filter_by(userid = current_user.id).first()
                id = producerdetails.producerid
                newcomp = Competitions(producerid = id, title=title, brief=brief, deadline=date, deadline_string=ISOtoDate(deadline))
                db.session.add(newcomp)
                db.session.commit()

                # Genre tags are added
                newcomp = Competitions.query.order_by(Competitions.compid.desc()).first()
                for genreid in genres:
                    newcomphas = CompHas(compid=newcomp.compid, genreid=genreid)
                    db.session.add(newcomphas)
                    db.session.commit()
                
                flask.flash("Competition created!")
                return flask.redirect(flask.url_for('comps.competitions'))
            
            except ValueError as e:
                flask.flash(str(e), category='error')

    return flask.render_template('create_post.html', user=current_user)
    
