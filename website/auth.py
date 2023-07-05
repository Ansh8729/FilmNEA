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

def send_email(sender, sender_password, receiver, msg):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender, sender_password)
    server.sendmail(sender, receiver, msg)
    server.quit()

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = Users.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                if user.accounttype == 2:
                    producer = Producers.query.filter_by(userid=user.id).first()
                    if producer.approved == 1:
                        flash("Logged in!", category='success')  
                        login_user(user, remember=True)
                        return redirect(url_for('views.home'))
                    else:
                        flash("Account is not authenticated.", category='error')  
                else:
                    flash("Logged in!", category='success')  
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
            if accounttype == "Screenwriter":
                new_user = Users(email=email, username=username, password=generate_password_hash(password1, method='scrypt'), accounttype = 1)
                db.session.add(new_user)
                new_writer = Screenwriters(userid=new_user.id)  
                db.session.add(new_writer)
                login_user(new_user, remember=True)
                flash('User created!', category='success')  
                db.session.commit()
                return redirect(url_for('views.home'))
            elif accounttype == "Producer":
                new_user = Users(email=email, username=username, password=generate_password_hash(password1, method='scrypt'), accounttype = 2)
                db.session.add(new_user)
                otp = ""
                for _ in range(6): 
                    num = random.randint(0, 9)
                    otp += str(num)
                new_producer = Producers(otp=otp)
                db.session.add(new_producer)
                msg = 'Hello, Your OTP is ' + otp
                send_email('writersworldnoreply@gmail.com', 'lolfruollznvecyd', email, msg)
                db.session.commit()
                return render_template("approval.html")

    return render_template("signup.html")


@auth.route("/approval", methods=['GET', 'POST'])
def approval():
    if request.method == 'POST':
        newproducer = Producers.query.order_by(Producers.producerid.desc()).first()
        code = request.form.get("otp")
        if code == newproducer.otp:
            new_user = Users.query.order_by(Users.id.desc()).first()
            newproducer.userid = new_user.id
            newproducer.approved = 1
            login_user(new_user, remember=True)
            flash('User created!', category='success')  
            db.session.commit()
            return redirect(url_for('views.home'))
        else:
            flash('Incorrect OTP.', category='error')

    return render_template("approval.html")

# The code below sends the user back to the home page when the user logs out.
@auth.route("/logout")
@login_required # This line restricts users from going on the home page without logging in.
def logout():
    logout_user()
    return redirect(url_for("views.home"))