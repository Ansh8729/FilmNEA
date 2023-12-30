import flask 
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers, Screenplays, LikedScreenplays, Comments, ScriptHas, Notifications, Awards
from werkzeug.utils import secure_filename
import os
import shutil
from werkzeug.utils import secure_filename
import uuid as uuid
from . import db
from .update import UpdateNotificationNumber, UpdateExperienceLevel
from .interact import CreateComment, DeleteComment, LikeExists, RateScreenplay, NotificationExists, ProducerResponse, ProducerRequest, DeletePost
from .subroutines import IncludesAtSymbol

profile = flask.Blueprint("profile", __name__)
    
@profile.route("/profilepage/<userid>")
@login_required
def profilepage(userid):
    UpdateNotificationNumber(current_user.id)
    profileuser = Users.query.filter_by(id=userid).first()

    if profileuser.accounttype == 1:
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
    UpdateNotificationNumber(current_user.id)
    if flask.request.method == "POST":
        try:
            profile = Users.query.filter_by(id = userid).first()
            file = flask.request.files['profilepic']
            bio = flask.request.form.get('bio')
            insta = flask.request.form.get('insta')
            twitter = flask.request.form.get('twitter')
            picturefilename = secure_filename(file.filename)
            namecheck = picturefilename.split(".")
            formats = ["png", "jpg"]

            # Profile picture validation
            if not file and profile.profilepic:
                profile.profilepic = profile.profilepic
                db.session.commit()
            elif file and namecheck[1] not in formats:
                raise ValueError("Invalid file format for profile picture.")
            elif file and namecheck[1] not in formats:
                picname = str(uuid.uuid1()) + "_" + picturefilename
                file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),'/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA',picname))
                shutil.move(picname,'static/images')
                profile = Users.query.filter_by(id = userid).first()
                profile.profilepic = picname
                db.session.commit()
            
            # Biography
            if not bio and profile.biography:
                profile.biography = profile.biography
                db.session.commit()
            elif bio:
                profile.biography = bio
                db.session.commit()
            
            # Instagram handle validation
            if not insta and profile.insta:
                profile.insta = profile.insta
                db.session.commit()
            elif insta and IncludesAtSymbol(insta) == False:
                raise ValueError("No @ included in Insta handle.")
            elif insta and IncludesAtSymbol(insta) == True:
                profile.insta = insta
                db.session.commit()

            # Twitter handle validation
            if not twitter and profile.twitter:
                profile.twitter = profile.twitter
                db.session.commit()
            elif twitter and IncludesAtSymbol(twitter) == False:
                ValueError("No @ included in Twitter handle.")
            elif twitter and IncludesAtSymbol(twitter) == True:
                profile.twitter = twitter
                db.session.commit()

            if current_user.accounttype == 1:
                writer = Screenwriters.query.filter_by(userid = userid).first()

                # Background colour and font style
                colour = flask.request.form.get('colorpicker')
                font = flask.request.form.get('fontstyle')
                if colour == '#ffffff' and writer.backgroundcolour:
                    writer.backgroundcolour = writer.backgroundcolour
                    db.session.commit()
                elif colour:
                    writer.backgroundcolour = colour
                    db.session.commit()

                if not font and writer.fontstyle:
                    writer.fontstyle = writer.fontstyle
                    db.session.commit()
                elif font: 
                    writer.fontstyle = font
                    db.session.commit()
        
            flask.flash("Edits made!")
            return flask.redirect(flask.url_for('profile.profilepage', userid=current_user.id))
        
        except ValueError as e:
            flask.flash(str(e), category="error")
            return flask.redirect(flask.url_for("profile.pageeditor", userid=current_user.id))
    
    return flask.render_template("pageeditor.html", user=current_user)

@profile.route("/pprate/<scriptid>", methods=['POST'])
@login_required
def rateonpp(scriptid):
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    writer = Screenwriters.query.filter_by(userid = script.writer.user.id).first()
    if LikeExists(writer.writerid, scriptid) == False:
        rating = flask.request.form.get("rate")
        RateScreenplay(writer.writerid, scriptid, rating)
        UpdateExperienceLevel(writer.user.id)
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
    else:
        flask.flash("You've already rated this screenplay!", category="error")
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))

@profile.route("/ppcreate-comment/<scriptid>", methods=['POST'])
@login_required
def ppcomment(scriptid):
    text = flask.request.form.get('text')
    if not text:
        flask.flash('Comment cannot be empty.', category='error')
    else:
        CreateComment(scriptid, current_user.id, text)
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))

@profile.route("/ppdelete-comment/<commentid>", methods=['GET', 'POST'])
@login_required
def deleteppcomment(commentid):
    DeleteComment(commentid)
    return flask.redirect(flask.url_for('profile.profilepage'))

@profile.route('/ppresponse/<scriptid>',methods=['POST'])
@login_required
def responseonpp(scriptid):
    producer = Producers.query.filter_by(userid = current_user.id).first()
    if NotificationExists(producer.producerid, scriptid, 1) == True:
        flask.flash("You've already sent a response for this script.")
        script = Screenplays.query.filter_by(scriptid=scriptid).first()
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
    else:
        response = flask.request.form.get('response')
        ProducerResponse(producer.producerid, scriptid, response)
        script = Screenplays.query.filter_by(scriptid=scriptid).first()
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
    
@profile.route('/pprequest/<scriptid>', methods=['POST'])
@login_required
def requestonpp(scriptid):
    producer = Producers.query.filter_by(userid = current_user.id).first()
    if NotificationExists(producer.producerid, scriptid, 2) == True:
        flask.flash("You've already sent a request for this script.")
        script = Screenplays.query.filter_by(scriptid=scriptid).first()
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
    else:
        ProducerRequest(producer.producerid, scriptid)
        script = Screenplays.query.filter_by(scriptid=scriptid).first()
        return flask.redirect(flask.url_for("profile.profilepage", userid = script.writer.user.id))
    
@profile.route("/ppdelete-post/<scriptid>/<userid>", methods=['POST'])
@login_required
def delete_postonpp(scriptid, userid):
    DeletePost(scriptid)
    return flask.redirect(flask.url_for("profile.profilepage", userid = userid))




