from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Users(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    forename = db.Column(db.String(75), unique=True)
    surname = db.Column(db.String(75))
    password = db.Column(db.String(150))
    accounttype = db.Column(db.Integer)
    profilepic = db.Column(db.String(), nullable=True) 
    biography = db.Column(db.Text)
    insta = db.Column(db.String(), nullable=True) 
    twitter = db.Column(db.String(), nullable=True) 
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())

    writers = db.relationship('Screenwriters', backref="user", passive_deletes=True)
    producers = db.relationship('Producers', backref="user", passive_deletes=True)
    
class Screenwriters(db.Model):
    __tablename__ = "Screenwriters"
    writerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.id'))
    backgroundcolour = db.Column(db.Integer)
    fontstyle = db.Column(db.String(30))
    experiencelevel = db.Column(db.Float)

    posts = db.relationship('Screenplays', backref="writer", passive_deletes=True)
    commenters = db.relationship('Comments', backref="writer", passive_deletes=True)
    responsees = db.relationship('Notifications', backref="writer", passive_deletes=True)
    likes = db.relationship('LikedScreenplays', backref="writer", passive_deletes=True)

class Screenplays(db.Model):
    __tablename__ = "Screenplays"
    scriptid = db.Column(db.Integer, primary_key=True)
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid', ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(300))
    logline = db.Column(db.String(165))
    message = db.Column(db.Text)
    screenplay = db.Column(db.String(300)) 
    fullfile = db.Column(db.String(300))
    avgrating = db.Column(db.Float)
    date_created = db.Column(db.Date, default=func.current_date())
    datetime_created = db.Column(db.DateTime(timezone=True), default=func.now())

    scripts = db.relationship('Notifications', backref="script", passive_deletes=True)
    scriptscommented = db.relationship('Comments', backref="script", passive_deletes=True)
    liked = db.relationship('LikedScreenplays', backref="script", passive_deletes=True)
    scripts2 = db.relationship('ScriptHas', backref="script", passive_deletes=True)
    liked2 = db.relationship('FeaturedScripts', backref="script", passive_deletes=True)

class ScriptHas(db.Model):
    __tablename__ = "ScriptHas"
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'), primary_key=True)
    genreid = db.Column(db.Integer, db.ForeignKey('Genres.genreid'), primary_key=True)

class Genres(db.Model):
    __tablename__ = "Genres"
    genreid = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(50))

    genres = db.relationship('ScriptHas', backref="has")
    genres2 = db.relationship('CompHas', backref="has")

class Producers(db.Model):
    __tablename__ = "Producers"
    producerid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('Users.id'))
    approved = db.Column(db.Integer)
    otp = db.Column(db.String(10))

    posts = db.relationship('Competitions', backref="producer", passive_deletes=True)
    responses = db.relationship('Notifications', backref="producer", passive_deletes=True)

class Notifications(db.Model):
    __tablename__ = "Notifications"
    notifid = db.Column(db.Integer, primary_key=True)
    responsetype = db.Column(db.Integer)
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'))
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'))
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'))
    requeststatus = db.Column(db.Integer)
    commentid = db.Column(db.Integer, db.ForeignKey('Comments.commentid'))
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'))
    submission = db.Column(db.String(150)) 
    ranking = db.Column(db.String(150))
    message = db.Column(db.Text)
    datetime_created = db.Column(db.DateTime(timezone=True))

class Competitions(db.Model):
    __tablename__ = "Competitions"
    compid = db.Column(db.Integer, primary_key=True)
    producerid = db.Column(db.Integer, db.ForeignKey('Producers.producerid'))
    title = db.Column(db.String(300))
    brief = db.Column(db.Text)
    deadline = db.Column(db.DateTime(timezone=True))
    deadline_string = db.Column(db.String(300))
    date_created = db.Column(db.String(300))
    datetime_created = db.Column(db.DateTime(timezone=True), default=func.now())
    submissionnum = db.Column(db.Integer)
    
    responses = db.relationship('Notifications', backref="comp", passive_deletes=True)
    awards = db.relationship('Awards', backref="comp", passive_deletes=True)

class CompHas(db.Model):
    __tablename__ = "CompHas"
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    genreid = db.Column(db.Integer, db.ForeignKey('Genres.genreid'), primary_key=True)

class LikedScreenplays(db.Model):
    __tablename__ = "LikedScreenplays"
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'), primary_key=True)
    rating = db.Column(db.Float)

class Comments(db.Model):
    __tablename__ = "Comments"
    commentid = db.Column(db.Integer, primary_key=True)
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'))
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'))
    comment = db.Column(db.String(300))
    datetime_created = db.Column(db.DateTime(timezone=True), default=func.now())
    
    responses = db.relationship('Notifications', backref="comment", passive_deletes=True)

class FeaturedScripts(db.Model):
    __tablename__ = "FeaturedScripts"
    featuredid = db.Column(db.Integer, primary_key=True)
    scriptid = db.Column(db.Integer, db.ForeignKey('Screenplays.scriptid'))
    dequeuedatetime = db.Column(db.DateTime(timezone=True))

class Awards(db.Model):
    __tablename__ = "Awards"
    writerid = db.Column(db.Integer, db.ForeignKey('Screenwriters.writerid'), primary_key=True)
    compid = db.Column(db.Integer, db.ForeignKey('Competitions.compid'), primary_key=True)
    ranking = db.Column(db.String(150))


    

