from flask import Blueprint, render_template
from flask_login import login_required, current_user

# The below code allows different routes to be stored.
views = Blueprint("views", __name__)

@views.route("/")
@views.route("/home")
@login_required # This line restricts users from going on the home page without logging in.
def home():
    return render_template("home.html", name=current_user.username) 
    #This line renders the home page using the HTML code in "home.html"
    