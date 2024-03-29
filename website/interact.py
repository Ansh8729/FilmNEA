import flask
from .models import Screenplays, Screenwriters, Notifications, Comments, LikedScreenplays, ScriptHas
from datetime import datetime
from . import db
import os
import shutil

def CreateComment(scriptid, userid, comment):
    post = Screenplays.query.filter_by(scriptid = scriptid).first()
    writer = Screenwriters.query.filter_by(userid = userid).first()
    if post:
        comment = Comments(writerid=writer.writerid, scriptid=scriptid, comment=comment)
        db.session.add(comment)
        db.session.commit()
        flask.flash("Comment created!")
        comment = Comments.query.order_by(Comments.commentid).first()
        writer2 = Screenwriters.query.filter_by(userid = post.writer.user.id).first()
        notif = Notifications(writerid = writer2.writerid, commentid=comment.commentid)
        db.session.add(notif)
        db.session.commit()
    else:
        flask.flash('Post does not exist.', category='error')

def DeleteComment(commentid):
    notif = Notifications.query.filter_by(commentid=commentid).first()
    if notif:
        db.session.delete(notif)
        db.session.commit()
    comment = Comments.query.filter_by(commentid=commentid).first()
    db.session.delete(comment)
    db.session.commit()
    flask.flash("Comment removed!")

def LikeExists(writerid, scriptid):
    like_exists = LikedScreenplays.query.filter(LikedScreenplays.writerid == writerid, scriptid==scriptid).first()
    if like_exists:
        return True
    else:
        return False

def RateScreenplay(writerid, scriptid, rating):
    newrating = LikedScreenplays(writerid = writerid, scriptid=scriptid, rating=rating)
    db.session.add(newrating)
    db.session.commit()
    flask.flash("Rating submitted!")
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    ratings = LikedScreenplays.query.filter_by(scriptid = scriptid)
    total = 0
    for record in ratings:
        total += record.rating
    script.avgrating = total/ratings.count()
    db.session.commit()

def NotificationExists(producerid, scriptid, type):
    notif_exists = Notifications.query.filter_by(producerid = producerid, scriptid = scriptid, responsetype = type).first()
    if notif_exists:
        return True
    else:
        return False

def ProducerResponse(producerid, scriptid, response):
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    newresponse = Notifications(producerid = producerid, writerid=script.writerid, scriptid=scriptid, message=response, responsetype = 1, datetime_created = datetime.now())
    db.session.add(newresponse)
    db.session.commit()
    flask.flash(f"Response sent!")

def ProducerRequest(producerid, scriptid):
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    newrequest = Notifications(producerid = producerid, writerid=script.writerid, scriptid=scriptid, responsetype = 2, requeststatus = 0, datetime_created = datetime.now())
    db.session.add(newrequest)
    db.session.commit()
    flask.flash(f"Request for full access for {script.title} sent!")

def DeletePost(scriptid):
    # 1. Delete all notifications relating to the post
    notifs = LikedScreenplays.query.filter_by(scriptid = scriptid)
    for notif in notifs:
        db.session.delete(notif)
        db.session.commit()

    # 2. Delete all of the post's ratings 
    ratings = LikedScreenplays.query.filter_by(scriptid = scriptid)
    for rating in ratings:
        db.session.delete(rating)
        db.session.commit()

    # 3. Delete all of the post's comments
    comments = Comments.query.filter_by(scriptid = scriptid)
    for comment in comments:
        db.session.delete(comment)
        db.session.commit()

    # 4. Delete all of the post's genre tags 
    scripthas = ScriptHas.query.filter_by(scriptid=scriptid)
    for record in scripthas:
        db.session.delete(record)
        db.session.commit()
    
    # 5. Delete the screenplay and its full file 
    post = Screenplays.query.filter_by(scriptid = scriptid).first()
    filepath = os.path.join('/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA/static/files',post.screenplay)
    os.remove(filepath)
    fullfilepath = os.path.join('/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA/static/files',post.fullfile)
    os.remove(fullfilepath)

    #6. Delete the post from the database
    db.session.delete(post)
    db.session.commit()
    flask.flash('Post deleted.', category='success')