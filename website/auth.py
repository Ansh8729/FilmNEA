from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import Users, Screenwriters, Producers, Genres
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, body, to_email, gmail_username, gmail_password):
    # Create a MIMEText object to represent the email body
    message = MIMEMultipart()
    message.attach(MIMEText(body, 'plain'))

    message['Subject'] = subject
    message['From'] = gmail_username
    message['To'] = to_email

    try:
        # Establish a connection to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        # Starts TLS encryption
        server.starttls()
        # Logs in to the NoReply gmail account
        server.login(gmail_username, gmail_password)
        # Sends the email
        server.sendmail(gmail_username, to_email, message.as_string())
        # Closes the SMTP server connection
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email could not be sent. Error: {str(e)}")

def LoadGenres():
    genrelist = ['Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sports', 'Thriller', 'Western']
    for i in range(len(genrelist)):
            newgenre = Genres(genre=genrelist[i])
            db.session.add(newgenre)
            db.session.commit()
    for i in Genres.query.all():
            if i.genreid > 13:
                db.session.delete(i)
                db.session.commit()

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = Users.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                if user.accounttype == "2":
                    producer = Producers.query.filter_by(userid = user.id).first()
                    if producer.approved == 0:
                        flash('User is not approved.', category='error')
                    else:
                        flash("Logged in!", category='success')
                        login_user(user, remember=True)
                        return redirect(url_for('homepage.home'))
                else:
                    flash("Logged in!", category='success')
                    login_user(user, remember=True)
                    return redirect(url_for('homepage.home'))
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

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

        if email_exists:
            flash('Email is already in use.', category='error')
        elif username_exists:
            flash('Username is already in use.', category='error')
        elif password1 != password2:
            flash("Passwords don't match!", category='error')
        elif len(username) < 2:
            flash('Username is too short.', category='error')
        elif len(password1) < 8:
            flash('Password is too short.', category='error')
        elif len(email) < 4:
            flash("Email is invalid.", category='error')
        else:
            names = username.split(" ")
            forename = names[0]
            surname = names[1]
            if accounttype == "Screenwriter":
                new_user = Users(email=email, username=username, forename=forename, surname=surname, password=generate_password_hash(
                password1, method='scrypt'), accounttype = 1)
                db.session.add(new_user)
                newuser = Users.query.order_by(Users.id.desc()).first()
                new_writer = Screenwriters(userid = newuser.id)
                db.session.add(new_writer)
                db.session.commit()
                genres = Genres.query.all()
                if genres:
                    login_user(new_user, remember=True)
                    flash('User created!')
                    return redirect(url_for('homepage.home'))
                else:
                    LoadGenres()
                    login_user(new_user, remember=True)
                    flash('User created!')
                    return redirect(url_for('homepage.home'))
            if accounttype == "Producer":
                new_user = Users(email=email, username=username, forename=forename, surname=surname, password=generate_password_hash(
                password1, method='scrypt'), accounttype = 2)
                db.session.add(new_user)
                db.session.commit()
                newuser = Users.query.order_by(Users.id.desc()).first()
                email = email.split("@")
                if email[1] == 'producersguild.org' or email[1] == "gmail.com":
                    otp = ""
                    for i in range(6):
                        num = random.randint(0,9)
                        otp += str(num)
                    msg = 'Hello, Your OTP is '+otp
                    new_producer = Producers(userid = newuser.id, otp=otp)
                    db.session.add(new_producer)
                    db.session.commit()
                    send_email('Writers World OTP Request', msg, newuser.email, 'writersworldnoreply@gmail.com', 'lolfruollznvecyd')
                    return redirect(url_for('auth.approval'))  
                else:
                    new_producer = Producers(userid = newuser.id)
                    db.session.add(new_producer)
                    db.session.commit()
                    login_user(new_user, remember=True)
                    flash('User created!')
                    return redirect(url_for('homepage.home'))

    return render_template("signup.html", user=current_user)

@auth.route("/approval", methods=['GET', 'POST'])
def approval():
    if request.method == 'POST':
        newproducer = Producers.query.order_by(Producers.producerid.desc()).first()
        code = request.form.get("otp")
        if code == newproducer.otp:
            newproducer = Producers.query.order_by(Producers.producerid.desc()).first()
            new_user = Users.query.order_by(Users.id.desc()).first()
            newproducer.approved = 1
            db.session.commit()
            login_user(new_user, remember=True)
            flash('User approved and created!', category='success')  
            return redirect(url_for('homepage.home'))
        else:
            flash('Incorrect OTP.', category='error')
            return redirect(url_for('auth.approval'))

    return render_template("approval.html")

@auth.route("/forgotpassword1", methods=['GET', 'POST'])
def forgotpassword1():
    if request.method == "POST":
        email = request.form.get("email")
        email_exists = Users.query.filter_by(email=email).first()
        if email_exists:
            return redirect(url_for("auth.forgotpassword2", email=email))
        else:
            flash("Email is not in database. Create an account.", category="error")
    return render_template("forgot_password1.html", user=current_user)

@auth.route("/forgotpassword2/<email>", methods=['GET', 'POST'])
def forgotpassword2(email):
    if request.method == "POST":
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        if password1 == password2:
            if len(password1) >= 8:
                password = generate_password_hash(password1, method='scrypt')
                user = Users.query.filter_by(email=email).first()
                user.password = password
                db.session.commit()
                flash("Password changed!", category="success")
                return redirect(url_for("auth.login"))
            else:
                flash("Password is too short.", category="error")
        else:
            flash("Passwords don't match.", category="error")

    return render_template("forgot_password2.html", user=current_user)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("homepage.home"))