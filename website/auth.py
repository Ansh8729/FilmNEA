from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import Users, Screenwriters, Producers, Genres
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
from .subroutines import SendEmail
from .load import LoadGenres

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try: 
            email = request.form.get("email")
            password = request.form.get("password")
            user = Users.query.filter_by(email=email).first()

            if not user:
                raise ValueError('Account does not exist.')
            elif not check_password_hash(user.password, password):
                raise ValueError('Password is incorrect.')
            
            if user.accounttype == 2:
                producer = Producers.query.filter_by(userid = user.id).first()
                email = email.split("@")
                # Producer accounts from the guild are not logged in if they haven't gotten approved via OTP verification
                if producer.approved == 0 and email[1] == 'producersguild.org': 
                    flash('User is not approved.', category='error')
                else:
                    flash("Logged in!", category='success')
                    login_user(user, remember=True)
                    return redirect(url_for('homepage.home'))
            else:
                flash("Logged in!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('homepage.home'))
            
        except ValueError as e:
            flash(str(e), category='error')

    return render_template("login.html", user=current_user)

@auth.route("/sign-up", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST': 
        try:
            email = request.form.get("email")
            username = request.form.get("username")
            password1 = request.form.get("password1")
            password2 = request.form.get("password2")
            accounttype = request.form.get("accounttype")

            email_exists = Users.query.filter_by(email=email).first()
            username_exists = Users.query.filter_by(username=username).first()

            if email_exists:
                raise ValueError('Email is already in use.')
            elif username_exists:
                raise ValueError('Username is already in use.')
            elif password1 != password2:
                raise ValueError("Passwords don't match!")
            elif len(username) < 6:
                raise ValueError('Username is too short.')
            elif len(password1) < 8:
                raise ValueError('Password is too short.')
            elif len(email) < 4:
                raise ValueError('Email is invalid.')

            names = username.split(" ")
            forename = names[0]
            surname = names[1]

            if accounttype == "Screenwriter":
                new_user = Users(email=email, username=username, forename=forename, surname=surname, password=generate_password_hash(
                    password1, method='scrypt'), accounttype=1)
                db.session.add(new_user)
                newuser = Users.query.order_by(Users.id.desc()).first()
                new_writer = Screenwriters(userid=newuser.id)
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

            elif accounttype == "Producer":
                new_user = Users(email=email, username=username, forename=forename, surname=surname, password=generate_password_hash(
                    password1, method='scrypt'), accounttype=2)
                db.session.add(new_user)
                db.session.commit()
                newuser = Users.query.order_by(Users.id.desc()).first()
                email_parts = email.split("@")

                if email_parts[1] == 'producersguild.org':
                    otp = "".join(str(random.randint(0, 9)) for _ in range(6))
                    msg = f'Hello, Your OTP is {otp}'
                    new_producer = Producers(userid=newuser.id, otp=otp)
                    db.session.add(new_producer)
                    db.session.commit()
                    SendEmail('Writers World OTP Request', msg, newuser.email, 'writersworldnoreply@gmail.com', 'lolfruollznvecyd')

                    # Redirect to OTP verification page
                    return redirect(url_for('auth.approval'))

                else:
                    new_producer = Producers(userid=newuser.id)
                    db.session.add(new_producer)
                    db.session.commit()
                    login_user(new_user, remember=True)
                    flash('User created!')
                    return redirect(url_for('homepage.home'))

        except ValueError as e:
            flash(str(e), category='error')
            return redirect(url_for('auth.signup'))

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
        try:
            password1 = request.form.get("password1")
            password2 = request.form.get("password2")
            if password1 != password2:
                raise ValueError("Passwords don't match.")
            elif len(password1) < 8:
                raise ValueError("Password is too short.")
            
            password = generate_password_hash(password1, method='scrypt')
            user = Users.query.filter_by(email=email).first()
            user.password = password
            db.session.commit()
            flash("Password changed!", category="success")
            return redirect(url_for("auth.login"))
        
        except ValueError as e:
            flash(str(e), category="error")

    return render_template("forgot_password2.html", user=current_user)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("homepage.home"))