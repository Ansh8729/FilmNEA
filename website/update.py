import datetime
from . import db
from .models import Screenwriters, Producers, Notifications, Screenplays, Awards, Competitions
from flask_login import current_user
from datetime import datetime

def UpdateNotificationNumber(userid): # Updates the badge indicating the number of unseen notification a user has 
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid=userid).first()
        notifs = Notifications.query.filter_by(writerid=writer.writerid)
        number = 0
        if notifs:
            for notif in notifs:
                if notif.commentid: # Comments 
                    number += 1
                if notif.producerid and notif.message and not notif.requeststatus and not notif.ranking: # Producer responses
                    number += 1
                if notif.producerid and notif.requeststatus == 0: # Producer requests 
                    number += 1
                if notif.compid and notif.message and notif.ranking: # Competition submissions being sent back
                    number += 1
            current_user.notifnum = number
            db.session.commit()
        else:
            current_user.notifnum = 0
            db.session.commit()

    if current_user.accounttype == 2:
        producer = Producers.query.filter_by(userid=userid).first()
        notifs = Notifications.query.filter_by(producerid=producer.producerid)
        number = 0
        if notifs:
            for notif in notifs:
                if notif.compid:
                    if not notif.ranking: # Competition submissions 
                        number += 1
                if notif.requeststatus == 1 or notif.requeststatus == 2: # Requests being returned 
                    number += 1
            current_user.notifnum = number
            db.session.commit()
        else:
            current_user.notifnum = 0
            db.session.commit()

def UpdateExperienceLevel(userid): # Updates a screenwriter user's experience level based on any new ratings and awards they've gotten
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
    writer.experiencelevel = (rating*scripts.count())+score
    db.session.commit()

def UpdateCompetitions(producerid): # Updates a producer's list of competitions by removing ones that are over
    comps = Competitions.query.filter_by(producerid=producerid)
    for comp in comps:
        notifs = Notifications.query.filter_by(compid = comp.compid and Notifications.message != None)
        if notifs.count() == 0 and datetime.now() > comp.deadline:
            db.session.delete(comp)
            db.session.commit()

def UpdateSubmissionNums(): # Updates the submission numbers for all competitions that are still running
    allcomps = Competitions.query.all()
    for comp in allcomps:
        submissions = Notifications.query.filter_by(compid = comp.compid)
        comp.submissionnum = submissions.count()
        db.session.commit()