# ====================== DATABASE MODELS ======================
import datetime
import uuid
from flask_login import UserMixin
from flask_restful import reqparse
from config import  db,ma,bcrypt


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    user_type = db.Column(db.Enum('Student', 'Staff', 'Faculty', 'Guest', 'Admin'), default='Guest')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy=True)
    activities = db.relationship('ActivityLog', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    session_id = db.Column(db.String(100))
    activity_type = db.Column(
        db.Enum('login', 'logout', 'chat_message', 'book_search', 'feedback', 'system_interaction'), nullable=False)
    activity_details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    message_id = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Enum('thumbs_up', 'thumbs_down', 'neutral'), nullable=False)
    comment = db.Column(db.Text)
    corrected_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ====================== MARSHMALLOW SCHEMAS ======================

class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User

    id = ma.auto_field()
    username = ma.auto_field()
    email = ma.auto_field()
    first_name = ma.auto_field()
    last_name = ma.auto_field()
    user_type = ma.auto_field()
    created_at = ma.auto_field()
    last_login = ma.auto_field()
    is_active = ma.auto_field()


class ActivityLogSchema(ma.SQLAlchemySchema):
    class Meta:
        model = ActivityLog

    id = ma.auto_field()
    activity_type = ma.auto_field()
    activity_details = ma.auto_field()
    timestamp = ma.auto_field()
    ip_address = ma.auto_field()


class FeedbackSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Feedback

    id = ma.auto_field()
    message_id = ma.auto_field()
    rating = ma.auto_field()
    comment = ma.auto_field()
    corrected_response = ma.auto_field()
    created_at = ma.auto_field()


# Initialize schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
activity_schema = ActivityLogSchema()
activities_schema = ActivityLogSchema(many=True)
feedback_schema = FeedbackSchema()
feedbacks_schema = FeedbackSchema(many=True)

# ====================== REQUEST PARSERS ======================

register_parser = reqparse.RequestParser()
register_parser.add_argument('username', type=str, required=True, help='Username is required')
register_parser.add_argument('email', type=str, required=True, help='Email is required')
register_parser.add_argument('password', type=str, required=True, help='Password is required')
register_parser.add_argument('first_name', type=str)
register_parser.add_argument('last_name', type=str)
register_parser.add_argument('user_type', type=str, choices=('Student', 'Staff', 'Faculty', 'Guest'), default='Guest')

login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str, required=True, help='Username is required')
login_parser.add_argument('password', type=str, required=True, help='Password is required')

chat_parser = reqparse.RequestParser()
chat_parser.add_argument('message', type=str, required=True, help='Message is required')
chat_parser.add_argument('session_id', type=str)

feedback_parser = reqparse.RequestParser()
feedback_parser.add_argument('message_id', type=str, required=True, help='Message ID is required')
feedback_parser.add_argument('rating', type=str, required=True, choices=('thumbs_up', 'thumbs_down', 'neutral'),
                             help='Rating is required')
feedback_parser.add_argument('comment', type=str)
feedback_parser.add_argument('corrected_response', type=str)

search_parser = reqparse.RequestParser()
search_parser.add_argument('q', type=str, required=True, help='Search query is required')
search_parser.add_argument('author', type=str)
search_parser.add_argument('subject', type=str)