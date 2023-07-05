from flask import Blueprint, render_template
from flask_login import login_required, current_user

views = Blueprint("views", __name__)

@views.route("/")
@views.route("/home")
@login_required
def home():
    return render_template("home.html", name=current_user.username)

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