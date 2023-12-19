import datetime
from . import db
from .models import Screenwriters, Producers, Notifications, Screenplays, Awards, Competitions
from flask_login import current_user
from datetime import datetime

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
        producer = Producers.query.filter_by(userid=userid).first()
        notifs = Notifications.query.filter_by(producerid=producer.producerid)
        if notifs:
            current_user.notifnum = notifs.count()
            db.session.commit()
        else:
            current_user.notifnum = 0
            db.session.commit()

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

def UpdateCompetitions(producerid):
    comps = Competitions.query.filter_by(producerid=producerid)
    for comp in comps:
        if comp.submissionnum == 0 and datetime.now() > comp.deadline:
            db.session.delete(comp)
            db.session.commit()