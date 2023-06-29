from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Users(db.Model, UserMixin):
    userid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    data_created = db.Column(db.DateTime(timezone=True), default=func.now())

class Screenwriters(db.Model):
    writerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.userid'))
    profilepic = db.Column(db.String(150))
    biography = db.Column(db.Text)
    backgroundcolour = db.Column(db.Integer)
    fontstyle = db.Column(db.Integer)
    experiencelevel = db.Column(db.Float)

class Producers(db.Model):
    producerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.userid'))
    profilepic = db.Column(db.String(150))
    biography = db.Column(db.Text)
    approved = db.Column(db.Integer)



