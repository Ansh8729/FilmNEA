from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers

views = Blueprint("views", __name__)

@views.route("/")
@views.route("/home")
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route("/profilepage")
@login_required
def profilepage():
    user = Users.query.filter_by(username = current_user.username).first()
    if user.accounttype == 1:
        details = Screenwriters.query.filter_by(userid = user.id).first()
    if user.accounttype == 2:
        details = Producers.query.filter_by(userid = user.id).first()
    return render_template("profilepage.html", user=current_user, details1=user, details2=details)

'''
@views.route("/<username>/profilepage")
@login_required
def profilepage():
    if current_user.accounttype == 1:
        writer = Screenwriters.query.filter_by(userid = current_user.id).first()
        return render_template("profilepage.html", writer=writer, user=current_user)
    if current_user.accounttype == 2:
        return render_template("producerpage.html")
''' 