"""
Application factory for the Intelligent Library Chat Assistant
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import Api
from .extensions import db, bcrypt, ma, login_manager

def create_app(config_class='config.DevelopmentConfig'):
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_class)

    # Override from environment variable if set
    if os.getenv('FLASK_CONFIG'):
        app.config.from_object(os.getenv('FLASK_CONFIG'))

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    ma.init_app(app)
    login_manager.init_app(app)

    from .model import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Initialize API
    api = Api(app)
    from .api.resources import (
        GetSession, RegisterResource, LoginResource, LogoutResource,
        ProfileResource, ChatResource, FeedbackResource, ActivityResource,
        BookSearchResource, AdminUsersResource, AdminActivitiesResource,
        AdminMetricsResource
    )
    api.add_resource(GetSession, '/api/session')
    api.add_resource(RegisterResource, '/api/register')
    api.add_resource(LoginResource, '/api/login')
    api.add_resource(LogoutResource, '/api/logout')
    api.add_resource(ProfileResource, '/api/profile')
    api.add_resource(ChatResource, '/api/chat')
    api.add_resource(FeedbackResource, '/api/feedback')
    api.add_resource(ActivityResource, '/api/activity')
    api.add_resource(BookSearchResource, '/api/search/books')
    api.add_resource(AdminUsersResource, '/api/admin/users')
    api.add_resource(AdminActivitiesResource, '/api/admin/activities')
    api.add_resource(AdminMetricsResource, '/api/admin/metrics')

    # Initialize CORS
    CORS(app, supports_credentials=True,
         origins=["http://localhost", "http://127.0.0.1:5500"],
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app
