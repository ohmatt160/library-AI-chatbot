"""
Application factory for the Intelligent Library Chat Assistant
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
import os

# Import blueprints
from api.routes import api_bp
from utils.database import db
from utils.logger import setup_logger


def create_app():
    """Create and configure the Flask application"""

    # Initialize Flask app
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Configuration
    app.config.from_object('config.Config')

    # Environment-specific configuration
    if os.getenv('FLASK_ENV') == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize database
    db.init_app(app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'api.login'

    # Setup logging
    setup_logger(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'library-chat-assistant'})

    # Root endpoint
    @app.route('/')
    def index():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Intelligent Library Chat Assistant</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { color: #2c3e50; }
                .links { margin-top: 30px; }
                .links a { display: inline-block; margin: 10px; padding: 10px 20px; 
                          background: #3498db; color: white; text-decoration: none; 
                          border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Intelligent Library Chat Assistant</h1>
                <p>Welcome to the AI-powered library assistance system</p>
                <div class="links">
                    <a href="/chat">Open Chat Interface</a>
                    <a href="/api/docs">API Documentation</a>
                    <a href="/admin">Admin Dashboard</a>
                </div>
                <div style="margin-top: 50px;">
                    <h3>System Information</h3>
                    <p><strong>Version:</strong> 1.0.0</p>
                    <p><strong>Status:</strong> <span style="color: green;">● Operational</span></p>
                </div>
            </div>
        </body>
        </html>
        '''

    return app