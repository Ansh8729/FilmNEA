from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app(): 
    # Initialises the secret key, the URI of the database and the folder where files are uploaded to
    app = Flask(__name__, static_folder="/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA/static")
    app.config['SECRET_KEY'] = "helloworld"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = '/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA'

    db.init_app(app)

    # The back-end files are imported and registered as blueprints 
    from .auth import auth
    from .homepage import homepage
    from .profile import profile
    from .comps import comps
    from .notifs import notifs
    from .screenplay import screenplay

    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(homepage, url_prefix="/")
    app.register_blueprint(comps, url_prefix="/")
    app.register_blueprint(profile, url_prefix="/")
    app.register_blueprint(notifs, url_prefix="/")
    app.register_blueprint(screenplay, url_prefix="/")

    from .models import Users
    from .load import LoadGenres

    # The app is created and the genres are added to the Genres table
    with app.app_context():
        db.create_all()
        LoadGenres()

    # The login system is set up 
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Users.query.get(id)
    
    return app
  