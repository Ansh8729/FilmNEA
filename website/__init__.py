from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__, static_folder="/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA/static")
    app.config['SECRET_KEY'] = "helloworld"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = '/Users/anshbindroo/Desktop/CSFilmNEA/FilmNEA'

    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models import Users, Genres

    with app.app_context():
        db.create_all()
        genrelist = ['Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sports', 'Thriller', 'Western']
        for i in range(len(genrelist)):
            newgenre = Genres(genre=genrelist[i])
            db.session.add(newgenre)
            db.session.commit()
        for i in Genres.query.all():
            if i.genreid > 13:
                db.session.delete(i)
                db.session.commit()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Users.query.get(id)
    
    return app
  