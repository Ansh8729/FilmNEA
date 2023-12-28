import flask 
from flask_login import login_required, current_user
from .models import Screenwriters, Producers, Screenplays, LikedScreenplays, Comments, Genres, ScriptHas, CompHas, FeaturedScripts
import uuid as uuid
from . import db
from .interact import CreateComment, DeleteComment, LikeExists, RateScreenplay, NotificationExists, ProducerResponse, ProducerRequest, DeletePost
from .update import UpdateNotificationNumber

screenplay = flask.Blueprint("screenplay", __name__)

@screenplay.route("/script/<scriptid>", methods=['GET', 'POST'])
@login_required
def script(scriptid):
    UpdateNotificationNumber(current_user.id)
    script = Screenplays.query.filter_by(scriptid=scriptid).first()
    scripthas = ScriptHas.query.all()
    comments = Comments.query.filter_by(scriptid=scriptid)
    return flask.render_template("script_full.html", post=script, scripthas=scripthas, user=current_user, comments=comments)

@screenplay.route("/rate2/<scriptid>", methods=['POST'])
@login_required
def rate(scriptid):
    writer = Screenwriters.query.filter_by(userid = current_user.id).first()
    if LikeExists(writer.writerid, scriptid) == False:
        rating = flask.request.form.get("rate")
        RateScreenplay(writer.writerid, scriptid, rating)
        return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))
    else:
        flask.flash("You've already rated this screenplay!", category="error")
        return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))

@screenplay.route("/create-comment2/<scriptid>", methods=['POST'])
@login_required
def create_comment(scriptid):
    text = flask.request.form.get('text')
    if not text:
        flask.flash('Comment cannot be empty.', category='error')
    else:
        CreateComment(scriptid, current_user.id, text)
        return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))

@screenplay.route("/delete-comment2/<scriptid>/<commentid>", methods=['GET', 'POST'])
@login_required
def delete_comment(scriptid, commentid):
    DeleteComment(commentid)
    return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))

@screenplay.route('/response2/<scriptid>',methods=['POST'])
@login_required
def response(scriptid):
    producer = Producers.query.filter_by(userid = current_user.id).first()
    if NotificationExists(producer.producerid, scriptid, 1) == True:
        flask.flash("You've already sent a response for this script.", category="error")
        return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))
    else:
        response = flask.request.form.get('response')
        ProducerResponse(producer.producerid, scriptid, response)
        return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))
    
@screenplay.route('/request2/<scriptid>', methods=['POST'])
@login_required
def request(scriptid):
    producer = Producers.query.filter_by(userid = current_user.id).first()
    if NotificationExists(producer.producerid, scriptid, 2) == True:
        flask.flash("You've already sent a request for this script.")
        return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))
    else:
        ProducerRequest(producer.producerid, scriptid)
        return flask.redirect(flask.url_for('screenplay.script', scriptid=scriptid))

@screenplay.route("/delete-post2/<scriptid>", methods=['POST'])
@login_required
def delete_post(scriptid):
    DeletePost(scriptid)
    return flask.redirect(flask.url_for('homepage.home'))