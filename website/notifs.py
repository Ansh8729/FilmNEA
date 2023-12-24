# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Screenwriters, Producers, Competitions, Notifications, Awards
import uuid as uuid
from . import db
from .update import UpdateNotificationNumber, UpdateExperienceLevel, UpdateCompetitions

notifs = flask.Blueprint("notifs", __name__)

@notifs.route('/notifications/<userid>', methods=['GET', 'POST'])
def notifications(userid):
    UpdateNotificationNumber(current_user.id)
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=userid).first()
        notifs = Notifications.query.filter_by(writerid = writer.writerid)
        return flask.render_template("notifications.html", notifs=notifs, user=current_user)
    if current_user.accounttype == 2:
        producer = Producers.query.filter_by(userid=userid).first()
        UpdateCompetitions(producer.producerid)
        notifs = Notifications.query.filter_by(producerid = producer.producerid)
        comps = Competitions.query.filter_by(producerid=producer.producerid)
        return flask.render_template("notifications.html", notifs=notifs, user=current_user, comps=comps)
    
@notifs.route('/sendback/<userid>/<compid>', methods=['GET', 'POST'])
@login_required
def sendback(userid, compid):
    UpdateNotificationNumber(current_user.id)
    if current_user.accounttype == 2:
        ranking = flask.request.form.get('ranking')
        response = flask.request.form.get('subresponse')
        producer = Producers.query.filter_by(userid=current_user.id).first()
        writer = Screenwriters.query.filter_by(userid=userid).first()  
        sub = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.writerid==writer.writerid, Notifications.compid == compid).first()
        sub.ranking = ranking
        sub.message = response
        db.session.commit()
        award = Awards(writerid = writer.writerid, compid=compid, ranking=ranking)
        db.session.add(award)
        db.session.commit()
        UpdateExperienceLevel(userid)
        flask.flash("Response sent!")
        return flask.redirect(flask.url_for("notifs.submissions", userid=current_user.id, compid=compid))
    else:
        flask.flash("That feature is only available for producers.", category="error")
        
@notifs.route('/deleteresponse/<responseid>', methods=['GET', 'POST'])
@login_required
def deleteresponse(responseid):
    response = Notifications.query.filter_by(notifid = responseid).first()
    db.session.delete(response)
    db.session.commit()
    flask.flash("Response removed!")
    return flask.redirect(flask.url_for("notifs.notifications", userid=current_user.id))

@notifs.route('/requestresponse/<requestid>', methods=['GET', 'POST'])
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
    return flask.redirect(flask.url_for("notifs.notifications", userid=current_user.id))

@notifs.route('/submissions/<compid>', methods=['GET', 'POST'])
@login_required
def submissions(compid):
    UpdateNotificationNumber(current_user.id)
    notifs = Notifications.query.filter_by(compid = compid, message = None, ranking = None)
    competition = Competitions.query.filter_by(compid=compid).first()
    return flask.render_template('submissions.html', notifs=notifs, user=current_user, comp=competition)

