from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
'''
    writers = db.relationship('Screenwriters', backref = 'Users')
    producers = db.relationship('Producers', backref = 'Users')

class Screenwriters(db.Model):
    writerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.id'))
    profilepic = db.Column(db.String(150)) #TO BE CHANGED
    biography = db.Column(db.Text)
    backgroundcolour = db.Column(db.Integer)
    fontstyle = db.Column(db.Integer)
    experiencelevel = db.Column(db.Float)
    screenplays = db.relationship('Screenplays', backref = 'Screenwriters')
    submissions = db.relationship('Submissions', backref = 'Screenwriters')
    responses = db.relationship('SubmissionResponses', backref = 'Screenwriters')
    liked = db.relationship('LikedScreenplays', backref = 'Screenwriters')

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
    scripthas = db.relationship('ScriptHas', backref = 'Screenplays')
    requests = db.relationship('Requests', backref = 'Screenplays')
    liked = db.relationship('LikedScreenplays', backref = 'Screenplays')

class ScriptHas(db.Model):
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'), primary_key=True)
    genreid = db.Column(db.Integer, primary_key=True)

class Genres(db.Model):
    genreid = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(50))

class Producers(db.Model):
    producerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.id'))
    profilepic = db.Column(db.String(150)) # TO BE CHANGED
    biography = db.Column(db.Text)
    approved = db.Column(db.Integer)
    requests = db.relationship('Requests', backref = 'Producers')
    competitions = db.relationship('Competitions', backref = 'Producers')
    responses = db.relationship('SubmissionResponses', backref = 'Producers')

class Requests(db.Model):
    requestid = db.Column(db.Integer, primary_key=True)
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'))
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'))
    granted = db.Column(db.Integer)

class Competitions(db.Model):
    compid = db.Column(db.Integer, primary_key=True)
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'))
    title = db.Column(db.String(300))
    brief = db.Column(db.Text)
    deadline = db.Column(db.DateTime(timezone=True))
    comphas = db.relationship('CompHas', backref = 'Competitions')
    submissions = db.relationship('Submissions', backref = 'Competitions')
    responses = db.relationship('SubmissionResponses', backref = 'Competitions')

class CompHas(db.Model):
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    genreid = db.Column(db.Integer, primary_key=True)

class Submissions(db.Model):
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    submission = db.Column(db.String(150)) # TO BE CHANGED
    submissiondate = db.Column(db.DateTime(timezone=True))

class SubmissionResponses(db.Model):
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'), primary_key=True)
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    message = db.Column(db.Text)

class LikedScreenplays(db.Model):
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'), primary_key=True)
    title = db.Column(db.String(300))
    rating = db.Column(db.Float)
    commented = db.Column(db.Integer)
'''