from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
ma = Marshmallow()
login_manager = LoginManager()
