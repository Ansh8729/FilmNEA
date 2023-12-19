import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Screenplays, LikedScreenplays, Comments, ScriptHas, Notifications, Awards
from werkzeug.utils import secure_filename
import os
import shutil
from werkzeug.utils import secure_filename
import uuid as uuid
from . import db
from .update import UpdateNotifications, UpdateExperienceLevel

profile = flask.Blueprint("profile", __name__)
    
@profile.route("/profilepage/<userid>")
@login_required
def profilepage(userid):
    UpdateNotifications(current_user.id)
    profileuser = Users.query.filter_by(id=userid).first()
    if profileuser.accounttype == 1:
        UpdateExperienceLevel(current_user.id)
        writer = Screenwriters.query.filter_by(userid=userid).first()
        scripts = Screenplays.query.filter_by(writerid = writer.writerid)
        comments = Comments.query.all()
        scripthas = ScriptHas.query.all()
        likes = LikedScreenplays.query.all()
        awards = Awards.query.filter_by(writerid = writer.writerid)
        return flask.render_template("profilepage.html", user=current_user, posts=scripts, comments=comments, scripthas=scripthas, profileuser=profileuser, details=writer, likes=likes, awards=awards)
    if profileuser.accounttype == 2:
        return flask.render_template("profilepage.html", user=current_user, profileuser=profileuser)

@profile.route("/pageeditor/<userid>", methods=['GET', 'POST'])
@login_required
def pageeditor(userid):
    UpdateNotifications(current_user.id)
    if flask.request.method == "POST":
        profile = Users.query.filter_by(id = userid).first()
        file = flask.request.files['profilepic']
        if not file:
            if profile.profilepic:
                profile.profilepic = profile.profilepic
                db.session.commit()
        else:
            picturefilename = secure_filename(file.filename)
            namecheck = picturefilename.split(".")
            formats = ["png", "jpg"]
            if namecheck[1] not in formats:
                flask.flash("Invalid file format for profile picture.", category="error")
                return flask.redirect(flask.url_for("profile.pageeditor", userid=current_user.id))
            else:
                picname = str(uuid.uuid1()) + "_" + picturefilename
                file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',picname))
                shutil.move(picname,'static/images')
                profile = Users.query.filter_by(id = userid).first()
                profile.profilepic = picname
                db.session.commit()
        bio = flask.request.form.get('bio')
        if not bio:
            if profile.biography:
                profile.biography = profile.biography
                db.session.commit()
        else:
            profile.biography = bio
            db.session.commit()
        insta = flask.request.form.get('insta')
        if not insta:
            if profile.insta:
                profile.insta = profile.insta
                db.session.commit()
        else:
            if "@" not in insta:
                flask.flash("No @ included in Insta handle.", category="error")
                return flask.redirect(flask.url_for("profile.pageeditor", userid=current_user.id))
            else:
                profile.insta = insta
                db.session.commit()
        twitter = flask.request.form.get('twitter')
        if not twitter:
            if profile.twitter:
                profile.twitter = profile.twitter
                db.session.commit()
        else:
            if "@" not in twitter:
                flask.flash("No @ included in Twitter handle.", category="error")
                return flask.redirect(flask.url_for("profile.pageeditor", userid=current_user.id))
            else:
                profile.twitter = twitter
                db.session.commit()
        if current_user.accounttype == 1:
            writer = Screenwriters.query.filter_by(userid = userid).first()
            colour = flask.request.form.get('colorpicker')
            if colour == '#ffffff':
                if writer.backgroundcolour:
                    writer.backgroundcolour = writer.backgroundcolour
                    db.session.commit()
            else:
                writer.backgroundcolour = colour
                db.session.commit()

            font = flask.request.form.get('fontstyle')
            if not font:
                if writer.fontstyle:
                    writer.fontstyle = writer.fontstyle
                    db.session.commit()
            else:
                writer = Screenwriters.query.filter_by(userid = userid).first()
                if font == 0:
                    writer.fontid = None
                else:
                    writer.fontstyle = font
                    db.session.commit()
        
            flask.flash("Edits made!")
            return flask.redirect(flask.url_for('profile.profilepage', userid=current_user.id))
        else:
            flask.flash("Edits made!")
            return flask.redirect(flask.url_for('profile.profilepage', userid=current_user.id))
    
    return flask.render_template("pageeditor.html", user=current_user)

@profile.route("/rate2/<userid>/<scriptid>", methods=['POST'])
@login_required
def rate2(scriptid, userid):
    rating = flask.request.form.get("rate")
    writer = Screenwriters.query.filter_by(userid = userid).first()
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    like_exists = LikedScreenplays.query.filter(LikedScreenplays.writerid == writer.writerid, LikedScreenplays.scriptid==scriptid).first()
    if not like_exists:
        newrating = LikedScreenplays(writerid = writer.writerid, scriptid=scriptid, rating=rating)
        db.session.add(newrating)
        db.session.commit()
        flask.flash("Rating submitted!")
    else:
        flask.flash("You've already rated this screenplay!", category="error")
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
    ratings = LikedScreenplays.query.filter_by(scriptid = scriptid)
    total = 0
    for i in ratings:
        total += i.rating
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    script.avgrating = total/ratings.count()
    db.session.commit()
    return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))

@profile.route("/profilepagecomment/<scriptid>", methods=['POST'])
@login_required
def ppcomment(scriptid):
    text = flask.request.form.get('text')
    if not text:
        flask.flash('Comment cannot be empty.', category='error')
    else:
        post = Screenplays.query.filter_by(scriptid = scriptid).first()
        writer = Screenwriters.query.filter_by(userid = current_user.id).first()
        if post:
            comment = Comments(writerid=writer.writerid, scriptid=scriptid, comment=text)
            db.session.add(comment)
            db.session.commit()
            comment = Comments.query.order_by(Comments.commentid).first()
            writer2 = Screenwriters.query.filter_by(userid = post.writer.user.id).first()
            notif = Notifications(writerid = writer2.writerid, responsetype = 3, commentid=comment.commentid)
            db.session.add(notif)
            db.session.commit()
        else:
            flask.flash('Post does not exist.', category='error')

    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))

@profile.route("/delete-comment2/<commentid>", methods=['GET', 'POST'])
@login_required
def deleteppcomment(commentid):
    notif = Notifications.query.filter_by(commentid=commentid).first()
    if notif:
        db.session.delete(notif)
        db.session.commit()
    comment = Comments.query.filter_by(commentid=commentid).first()
    db.session.delete(comment)
    db.session.commit()
    flask.flash("Comment removed!")
    return flask.redirect(flask.url_for('profile.profilepage'))

@profile.route('/response2/<scriptid>',methods=['POST'])
@login_required
def response2(scriptid):
    response = flask.request.form.get('response')
    request = flask.request.form.get('request')
    if response:
        producer = Producers.query.filter_by(userid = current_user.id).first()
        response_exists = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.scriptid == scriptid, Notifications.responsetype == 1).first()
        if response_exists:
            flask.flash("You've already sent a response for this script.")
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
        else:
            producer = Producers.query.filter_by(userid = current_user.id).first()
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            newresponse = Notifications(producerid = producer.producerid, writerid=script.writerid, scriptid=scriptid, message=response, responsetype = 1)
            db.session.add(newresponse)
            db.session.commit()
            flask.flash(f"Response sent!")
        script = Screenplays.query.filter_by(scriptid=scriptid).first()
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
    elif request:
        producer = Producers.query.filter_by(userid = current_user.id).first()
        request_exists = Notifications.query.filter(Notifications.producerid == producer.producerid, Notifications.scriptid == scriptid, Notifications.responsetype == 2).first()
        if request_exists:
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
        else:
            producer = Producers.query.filter_by(userid = current_user.id).first()
            script = Screenplays.query.filter_by(scriptid=scriptid).first()
            newrequest = Notifications(producerid = producer.producerid, writerid=script.writerid, scriptid=scriptid, responsetype = 2, requeststatus = 0)
            db.session.add(newrequest)
            db.session.commit()
            flask.flash(f"Request for full access for {script.title} sent!")
        script = Screenplays.query.filter_by(scriptid=scriptid).first()
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))



