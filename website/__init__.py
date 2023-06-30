from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path 
from flask_login import LoginManager
#import 

db = SQLAlchemy()
DB_NAME = "database.db"

# Folder below is given a name so that it can be imported into the main Python file "app.py"
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "helloworld"
        #Secret key used to encrypt session data
    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # The below code registers the blueprints with the application.
    from .views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
        
    from .models import Users
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Users.query.get(int(id))

    return app 

  