# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Competitions, Genres, CompHas, Notifications
from wtforms import widgets, SelectMultipleField
from werkzeug.utils import secure_filename
import os
import shutil
from werkzeug.utils import secure_filename
import uuid as uuid
from . import db
from datetime import datetime, timedelta, date
from .subroutines import NoSpaces, IsPDF
from .update import UpdateNotificationNumber, UpdateSubmissionNums

comps = flask.Blueprint("comps", __name__)
    
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

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
    UpdateNotificationNumber(current_user.id)
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
    scriptname = NoSpaces(secure_filename(file.filename))
    file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',scriptname)) 
    shutil.move(scriptname,'static/files')
    if IsPDF(file.filename) == False:
        flask.flash("Upload a PDF!", category='error')
    else:
        writer = Screenwriters.query.filter_by(userid=current_user.id).first()
        comp = Competitions.query.filter_by(compid=compid).first()
        newsub = Notifications(writerid=writer.writerid, producerid=comp.producerid, compid=compid, submission=scriptname)
        db.session.add(newsub)
        db.session.commit()
        flask.flash("Submission sent!")
        return flask.redirect(flask.url_for("comps.competitions"))
    
@comps.route("delete-comp/<compid>", methods=['POST'])
@login_required
def delete_comp(compid):
    compsubs = Notifications.query.all()
    for i in compsubs:
        if i.compid == compid:
            db.session.delete(i)
            db.session.commit()
    compgenres = CompHas.query.all()
    for i in compgenres:
        if i.compid == compid:
            db.session.delete(i)
            db.session.commit()
    comp = Competitions.query.filter_by(compid=compid).first()
    db.session.delete(comp)
    db.session.commit()
    flask.flash('Competition deleted.', category='success')
    return flask.redirect(flask.url_for('comps.competitions'))