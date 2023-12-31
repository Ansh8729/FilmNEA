import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Competitions, Genres, CompHas, Notifications
from werkzeug.utils import secure_filename
import os
import shutil
import uuid as uuid
from . import db
from datetime import datetime, timedelta, date
from .subroutines import NoSpaces
from .pdf import IsPDF
from .update import UpdateNotificationNumber, UpdateSubmissionNums

comps = flask.Blueprint("comps", __name__)

@comps.route("/competitions", methods=['GET', 'POST'])
@login_required
def competitions():
    UpdateNotificationNumber(current_user.id)
    UpdateSubmissionNums()
    comps = Competitions.query.filter(datetime.now() < Competitions.deadline).order_by(Competitions.submissionnum.desc())
    comphas = CompHas.query.all()
    return flask.render_template("competitions.html", user=current_user, comps=comps, comphas=comphas)

@comps.route("/sort2", methods=['GET','POST'])
@login_required
def sort2():
    UpdateNotificationNumber(current_user.id)
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
    UpdateNotificationNumber(current_user.id)
    comphas = CompHas.query.all()
    genre = flask.request.form.get("genre")
    
    if genre == "0":
        return flask.redirect(flask.url_for("comps.competitions"))
    else:
        genrename = Genres.query.filter_by(genreid=genre).first()
        compids = CompHas.query.filter_by(genreid=genre).all()
        comps = []
        for comp in compids:
            comp = Competitions.query.filter_by(compid=comp.compid).first()
            comps.append(comp)
        if genre == "1":
            flask.flash(f"Now showing all competitions that accept all genres.")
        else:
            flask.flash(f"Now showing all {genrename.genre} competitions.")
        
        return flask.render_template("competitions.html", user=current_user, comps=comps, comphas=comphas)

@comps.route('/comp/<compid>', methods=['GET', 'POST'])
@login_required
def comp(compid):
    UpdateNotificationNumber(current_user.id)
    comp = Competitions.query.filter_by(compid = compid).first()
    writer = Screenwriters.query.filter_by(userid=current_user.id).first()
    notif = Notifications.query.filter_by(writerid = writer.writerid, compid = compid).first()

    if notif:
        submitted = True
    else:
        submitted = False

    return flask.render_template("comp_full.html",user=current_user, comp=comp, submitted=submitted)

@comps.route('/submit/<compid>', methods=['GET', 'POST'])
@login_required
def submit(compid):
    file = flask.request.files['submission']
    scriptname = NoSpaces(secure_filename(file.filename))
    file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 

    if IsPDF(file.filename) == False:
        os.remove(file.filename)
        flask.flash("Upload a PDF!", category='error')
        return flask.redirect(flask.url_for("comps.comp", compid=compid))
    else:
        shutil.move(scriptname,'static/files')
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        comp = Competitions.query.filter_by(compid=compid).first()
        newsub = Notifications(writerid=writer.writerid, producerid=comp.producerid, compid=compid, submission=scriptname, datetime_created = datetime.now())
        db.session.add(newsub)
        db.session.commit()
        flask.flash("Submission sent!")
        return flask.redirect(flask.url_for("comps.competitions"))
    
@comps.route("/delete-comp/<compid>", methods=['GET', 'POST'])
@login_required
def delete_comp(compid):
    
    #1. Delete all submissions 
    submissions = Notifications.query.filter_by(compid=compid)
    for record in submissions:
        filepath = os.path.join('/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA/static/files',record.submission)
        os.remove(filepath)
        db.session.delete(record)
        db.session.commit()

    #2. Delete all genre tags
    compgenres = CompHas.query.filter_by(compid=compid)
    for record in compgenres:
        db.session.delete(record)
        db.session.commit()
    
    #3. Delete competition
    comp = Competitions.query.filter_by(compid=compid).first()
    db.session.delete(comp)
    db.session.commit()
    flask.flash('Competition deleted.', category='success')
    return flask.redirect(flask.url_for('comps.competitions'))