from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import Users, Screenwriters, Producers
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import smtplib
from email.message import EmailMessage
import ssl

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = Users.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category='sucess')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html")

@auth.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get("email")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        accounttype = request.form.get("accounttype")
    
        email_exists = Users.query.filter_by(email=email).first()
        username_exists = Users.query.filter_by(username=username).first()

        # The below IF statement validates the inputs.
        if email_exists:
            flash('Email is already in use.', category='error')
        elif username_exists:
            flash('Username is already in use.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match!', category='error')
        elif len(username) < 2:
            flash('Username is too short.', category='error')
        elif len(password1) < 6:
            flash('Password is too short.', category='error')
        elif len(email) < 4:
            flash('Email is invalid.', category='error')
        else:
            new_user = Users(email=email, username=username, password=generate_password_hash(password1, method='scrypt'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('User created!')
            if accounttype == "Screenwriter":
                newwriter = Users.query.order_by(Users.id.desc()).first()
                new_writer = Screenwriters(userid = newwriter.id)
                db.session.add(new_writer)
                db.session.commit()
                return redirect(url_for('views.home'))
            elif accounttype == "Producer":
                newproducer = Users.query.order_by(Users.id.desc()).first()
                new_producer = Producers(userid = newproducer.id)
                db.session.add(new_producer)
                db.session.commit()
                return redirect(url_for('views.home'))

    return render_template("signup.html")

'''
@auth.route("/approval", methods=['GET', 'POST'])
def approval():
    newproducer = Users.query.order_by(Users.id.desc()).first()
    email_sender = 'writersworldnoreply@gmail.com'
    email_password = 'lolfruollznvecyd'
    email_receiver = 'bindrooansh@gmail.com'
    subject = 'WritersWorld Producer Authentication'
    otp = ''.join([str(random.randint(0,9))] for i in range(6))
    body = 'Hello, Your OTP is '+str(otp)
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['subject'] = subject
    em.set_content(body)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 587, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())

    if request.method == 'POST':
        code = request.form.get("otp")
        if code == otp:
            return redirect(url_for('views.home'))
        else:
            flash('Incorrect OTP.', category='error')
'''

# The code below sends the user back to the home page when the user logs out.
@auth.route("/logout")
@login_required # This line restricts users from going on the home page without logging in.
def logout():
    logout_user()
    return redirect(url_for("views.home"))