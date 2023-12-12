# from flask import Blueprint, render_template, request, flash, redirect, url_for
import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Competitions, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, Notifications, Awards
import uuid as uuid
from . import db
import datetime

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
        day = daynum+"nd"
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

def UpdateExperienceLevel(userid):
    writer = Screenwriters.query.filter_by(userid=userid).first()
    scripts = Screenplays.query.filter_by(writerid = writer.writerid)
    rating = 0
    for script in scripts:
        if script.avgrating != None:
            rating += script.avgrating
    score = 0
    awards = Awards.query.filter_by(writerid = writer.writerid)
    for award in awards:
        if award.ranking == "1st":
            score += 3
        if award.ranking == "2nd":
            score += 2
        if award.ranking == "3rd":
            score += 1
        writer.experiencelevel = rating*scripts.count()+score
        db.session.commit()

def UpdateNotifications(userid):
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=userid).first()
        notifs = Notifications.query.filter_by(writerid=writer.writerid)
        if notifs:
            current_user.notifnum = notifs.count()
            db.session.commit()
        else:
            current_user.notifnum = 0
            db.session.commit()
    if current_user.accounttype == 2:
        producer = Producers.query.filter_by(userid=userid)
        notifs = Notifications.query.filter_by(producerid=producer.producerid)
        if notifs:
            current_user.notifnum = notifs.count()
            db.session.commit()
        else:
            current_user.notifnum = 0
            db.session.commit()

def UpdateCompetitions(producerid):
    comps = Competitions.query.filter_by(producerid=producerid)
    for comp in comps:
        if comp.submissionnum == 0 and datetime.now() > comp.deadline:
            db.session.delete(comp)
            db.session.commit()

notifs = flask.Blueprint("notifs", __name__)

@notifs.route('/notifications/<userid>', methods=['GET', 'POST'])
@login_required
def notifications(userid):
    UpdateNotifications(current_user.id)
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
    UpdateNotifications(current_user.id)
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
    UpdateNotifications(current_user.id)
    notifs = Notifications.query.filter_by(compid = compid)
    competition = Competitions.query.filter_by(compid=compid).first()
    return flask.render_template('submissions.html', notifs=notifs, user=current_user, comp=competition)

