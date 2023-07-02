from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Users(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())

class Screenwriters(db.Model):
    __tablename__ = "Screenwriters"
    writerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.id'))
    profilepic = db.Column(db.String(150)) #TO BE CHANGED
    biography = db.Column(db.Text)
    backgroundcolour = db.Column(db.Integer)
    fontstyle = db.Column(db.Integer)
    experiencelevel = db.Column(db.Float)

class BGColours(db.Model):
    __tablename__ = "BGColours"
    backgroundcolour = db.Column(db.Integer, primary_key=True)
    colour = db.Column(db.String(150), primary_key=True)

class FontStyles(db.Model):
    __tablename__ = "FontStyles"
    fontstyle = db.Column(db.Integer, primary_key=True)
    font = db.Column(db.String(150), primary_key=True)

class Screenplays(db.Model):
    __tablename__ = "Screenplays"
    scriptid = db.Column(db.Integer, primary_key=True)
    writerid = db.Column(db.Integer)
    title = db.Column(db.String(300))
    logline = db.Column(db.String(165))
    message = db.Column(db.Text)
    screenplay = db.Column(db.String(300)) #TO BE CHANGED
    data_created = db.Column(db.DateTime(timezone=True), default=func.now())
    avgrating = db.Column(db.Float)

class ScriptHas(db.Model):
    __tablename__ = "ScriptHas"
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'), primary_key=True)
    genreid = db.Column(db.Integer, primary_key=True)

class Genres(db.Model):
    __tablename__ = "Genres"
    genreid = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(50))

class Producers(db.Model):
    __tablename__ = "Producers"
    producerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.id'))
    profilepic = db.Column(db.String(150)) # TO BE CHANGED
    biography = db.Column(db.Text)
    approved = db.Column(db.Integer)

class Requests(db.Model):
    __tablename__ = "Requests"
    requestid = db.Column(db.Integer, primary_key=True)
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'))
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'))
    granted = db.Column(db.Integer)

class Competitions(db.Model):
    __tablename__ = "Competitions"
    compid = db.Column(db.Integer, primary_key=True)
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'))
    title = db.Column(db.String(300))
    brief = db.Column(db.Text)
    deadline = db.Column(db.DateTime(timezone=True))

class CompHas(db.Model):
    __tablename__ = "CompHas"
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    genreid = db.Column(db.Integer, primary_key=True)

class Submissions(db.Model):
    __tablename__ = "Submissions"
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    submission = db.Column(db.String(150)) # TO BE CHANGED
    submissiondate = db.Column(db.DateTime(timezone=True))

class SubmissionResponses(db.Model):
    __tablename__ = "SubmissionResponses"
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'), primary_key=True)
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    message = db.Column(db.Text)

class LikedScreenplays(db.Model):
    __tablename__ = "LikedScreenplays"
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'), primary_key=True)
    title = db.Column(db.String(300))
    rating = db.Column(db.Float)
    commented = db.Column(db.Integer)