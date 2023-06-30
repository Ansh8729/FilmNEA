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
    profilepic = db.Column(db.String(150)) #TO BE CHANGED
    biography = db.Column(db.Text)
    backgroundcolour = db.Column(db.Integer)
    fontstyle = db.Column(db.Integer)
    experiencelevel = db.Column(db.Float)

class BGColours(db.Model):
    backgroundcolour = db.Column(db.Integer, primary_key=True)
    colour = db.Column(db.String(150), primary_key=True)

class FontStyles(db.Model):
    fontstyle = db.Column(db.Integer, primary_key=True)
    font = db.Column(db.String(150), primary_key=True)

class Screenplays(db.Model):
    scriptid = db.Column(db.Integer, primary_key=True)
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'))
    title = db.Column(db.String(300))
    logline = db.Column(db.String(165))
    message = db.Column(db.Text)
    screenplay = db.Column(db.String(300)) #TO BE CHANGED
    data_created = db.Column(db.DateTime(timezone=True), default=func.now())
    avgrating = db.Column(db.Float)

class ScriptHas(db.Model):
    scriptid = db.Column(db.Integer, primary_key=True)
    genreid = db.Column(db.Integer, primary_key=True)

class ScriptHas(db.Model):
    genreid = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(50))

class Producers(db.Model):
    producerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.userid'))
    profilepic = db.Column(db.String(150))
    biography = db.Column(db.Text)
    approved = db.Column(db.Integer)

class Requests(db.Model):
    requestid = db.Column(db.Integer, primary_key=True)
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'))
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'))
    granted = db.Column(db.Integer)



