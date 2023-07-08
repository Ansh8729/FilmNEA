from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from .models import Users, Screenwriters, Producers
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, TextAreaField, SelectField

views = Blueprint("views", __name__)

class ProfilePageForm(FlaskForm):
    profilepic = FileField("Profile Picture")
    biography = TextAreaField("Biography")
    bgcolour = SelectField("Background Colour", choices=[('1', 'Red'), ('2', 'Yellow'), ('3', 'Blue')])
    fontstyle = SelectField("Font Style", choices=[('1', 'Default'), ('2', 'Arial'), ('3', 'Impact')])
    submit = SubmitField("Submit")

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
    elif user.accounttype == 2:
        details = Producers.query.filter_by(userid = user.id).first()

    return render_template("profilepage.html", user=current_user, details1=user, details2=details)

@views.route("/pageeditor", methods=['GET', 'POST'])
@login_required
def pageeditor():
    form = ProfilePageForm()
    # if form.validate_on_submit():
    return render_template("pageeditor.html", form=form, user=current_user)