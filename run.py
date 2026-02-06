import uuid
import time
from datetime import datetime, timedelta
import json
from flask import request, jsonify, session
from flask_login import  login_user, logout_user, login_required, current_user
from flask_restful import Resource

from app.model import ActivityLog, db, User, register_parser, user_schema, login_parser, UserSession, chat_parser, \
    feedback_parser, Feedback, activities_schema, search_parser, users_schema, activity_schema
from config import login_manager, api, dialogue_manager, metrics_tracker, app, opac_client

# ====================== FLASK-LOGIN SETUP ======================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def get_client_info():
    return {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')
    }


def log_activity(user_id, session_id, activity_type, details):
    client_info = get_client_info()
    activity = ActivityLog(
        user_id=user_id,
        session_id=session_id,
        activity_type=activity_type,
        activity_details=details,
        **client_info
    )
    db.session.add(activity)
    db.session.commit()


# ====================== RESOURCE CLASSES ======================
class GetSession(Resource):
    def get(self):
        """Get or create a session"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        return jsonify({
            'session_id': session['session_id'],
            'user_authenticated': current_user.is_authenticated
        })
api.add_resource(GetSession, '/api/session')

class RegisterResource(Resource):
    def post(self):
        """Register a new user"""
        args = register_parser.parse_args()

        # Check if user exists
        if User.query.filter_by(username=args['username']).first():
            return {'error': 'Username already exists'}, 400

        if User.query.filter_by(email=args['email']).first():
            return {'error': 'Email already exists'}, 400

        # Create new user
        user = User(
            username=args['username'],
            email=args['email'],
            first_name=args.get('first_name', ''),
            last_name=args.get('last_name', ''),
            user_type=args.get('user_type', 'Guest')
        )
        user.set_password(args['password'])

        db.session.add(user)
        db.session.commit()

        # Log activity
        log_activity(user.id, session.get('session_id', 'registration'), 'system_interaction', {
            'action': 'user_registration'
        })

        return {
            'status': 'success',
            'message': 'User created successfully',
            'user': user_schema.dump(user)
        }, 201


class LoginResource(Resource):
    def post(self):
        """Login user"""
        args = login_parser.parse_args()

        user = User.query.filter_by(username=args['username']).first()
        if not user or not user.check_password(args['password']):
            return {'error': 'Invalid username or password'}, 401

        if not user.is_active:
            return {'error': 'Account is deactivated'}, 403

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Login user
        login_user(user)

        # Generate session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        # Create session record
        client_info = get_client_info()
        user_session = UserSession(
            user_id=user.id,
            session_id=session['session_id'],
            **client_info
        )
        db.session.add(user_session)
        db.session.commit()

        # Log activity
        log_activity(user.id, session['session_id'], 'login', {'method': 'password'})

        return {
            'status': 'success',
            'user_id': user.id,
            'username': user.username,
            'user_type': user.user_type,
            'session_id': session['session_id']
        }


class LogoutResource(Resource):
    @login_required
    def post(self):
        """Logout user"""
        # Log activity
        log_activity(current_user.id, session.get('session_id'), 'logout', {})

        # End session
        if 'session_id' in session:
            session_record = UserSession.query.filter_by(
                session_id=session['session_id'],
                is_active=True
            ).first()
            if session_record:
                session_record.logout_time = datetime.utcnow()
                session_record.is_active = False
                db.session.commit()

        logout_user()
        session.clear()

        return {'status': 'success', 'message': 'Logged out'}


class ProfileResource(Resource):
    @login_required
    def get(self):
        """Get current user profile"""
        return user_schema.dump(current_user)


class ChatResource(Resource):
    def post(self):
        """Handle chat messages"""
        args = chat_parser.parse_args()

        # Generate or get session ID
        session_id = args.get('session_id') or session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

        # Get user ID
        user_id = current_user.id if current_user.is_authenticated else f"anon_{session_id}"

        # Track response time
        start_time = time.time()

        try:
            print(f"🔍 DEBUG: Processing message: {args['message']}")
            print(f"🔍 DEBUG: User ID: {user_id}, Session ID: {session_id}")
            # Process message through dialogue manager
            result = dialogue_manager.process_message(
                user_id=user_id,
                session_id=session_id,
                message=args['message']
            )
            print(f"🔍 DEBUG: Result keys: {result.keys()}")
            print(f"🔍 DEBUG: Response type: {type(result.get('response'))}")
            print(
                f"🔍 DEBUG: Response preview: {str(result.get('response'))[:200] if result.get('response') else 'None'}")
            # VALIDATE RESULT
            required_keys = ['response', 'confidence', 'processing_method']
            for key in required_keys:
                if key not in result:
                    print(f"❌ ERROR: Missing key '{key}' in result")
                    print(f"❌ Result keys: {result.keys()}")
                    raise KeyError(f"Missing required key in result: {key}")

            # Validate response is a string and not empty
            if not isinstance(result['response'], str):
                print(f"❌ ERROR: Response is not a string. Type: {type(result['response'])}")
                result['response'] = str(result['response'])

            if not result['response']:
                print(f"⚠️ WARNING: Empty response, using fallback")
                result['response'] = "I'm here to help with library services."

            # Validate confidence is a number
            if not isinstance(result['confidence'], (int, float)):
                print(f"⚠️ WARNING: Confidence is not a number. Type: {type(result['confidence'])}")
                result['confidence'] = 0.0
        except Exception as e:
            print(f"❌ ERROR in dialogue_manager.process_message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': 'Processing error', 'message': str(e)}, 500

        # Calculate response time
        response_time = (time.time() - start_time) * 1000

        # Log chat activity for authenticated users
        if current_user.is_authenticated:
            log_activity(current_user.id, session_id, 'chat_message', {
                'message': args['message'],
                'response_time_ms': response_time,
                'confidence': result.get('confidence', 0),
                'intent': result.get('intent', 'unknown')
            })

        # Track metrics
        metrics_tracker.record_interaction(
            user_id=user_id,
            session_id=session_id,
            message=args['message'],
            response=result['response'],
            response_time=response_time,
            confidence=result['confidence'],
            method=result.get('processing_method', 'unknown')
        )

        return {
            'response': result['response'],
            'session_id': session_id,
            'response_time_ms': round(response_time, 2),
            'confidence': round(result['confidence'], 3),
            'processing_method': result['processing_method'],
            'suggested_follow_ups': result.get('suggested_follow_ups', []),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_authenticated': current_user.is_authenticated,
            'user_type': current_user.user_type if current_user.is_authenticated else 'Guest'
        }


class FeedbackResource(Resource):
    # @login_required
    def post(self):
        """Submit feedback"""
        args = feedback_parser.parse_args()

        # Create feedback
        feedback = Feedback(
            user_id=current_user.id,
            message_id=args['message_id'],
            rating=args['rating'],
            comment=args.get('comment', ''),
            corrected_response=args.get('corrected_response', '')
        )

        db.session.add(feedback)
        db.session.commit()

        # Log activity
        log_activity(current_user.id, session.get('session_id'), 'feedback', {
            'message_id': args['message_id'],
            'rating': args['rating']
        })

        # Update learning models if needed
        if args['rating'] == 'thumbs_down' and args.get('corrected_response'):
            # update_knowledge_base(...) - implement this
            pass

        return {
            'status': 'success',
            'feedback_id': feedback.id,
            'message': 'Thank you for your feedback!'
        }


class ActivityResource(Resource):
    @login_required
    def get(self):
        """Get user's activity logs"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        activities = ActivityLog.query.filter_by(user_id=current_user.id) \
            .order_by(ActivityLog.timestamp.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return {
            'activities': activities_schema.dump(activities.items),
            'total': activities.total,
            'page': activities.page,
            'per_page': activities.per_page,
            'total_pages': activities.pages
        }


class BookSearchResource(Resource):
    # @login_required
    def get(self):
        """Search books"""
        args = search_parser.parse_args()

        # Log search activity
        log_activity(current_user.id, session.get('session_id'), 'book_search', {
            'query': args['q'],
            'author': args.get('author'),
            'subject': args.get('subject')
        })

        # Search local database (placeholder)
        local_results = []

        # Search OPAC system if configured
        if app.config.get('OPAC_INTEGRATION'):
            opac_results = opac_client.search(args['q'], args.get('author'), args.get('subject'))
            results = local_results + opac_results
        else:
            results = local_results

        return {
            'query': args['q'],
            'count': len(results),
            'results': results[:20],
            'source': 'local+opac' if app.config.get('OPAC_INTEGRATION') else 'local'
        }


# ====================== ADMIN RESOURCES ======================

class AdminUsersResource(Resource):
    @login_required
    def get(self):
        """Get all users (admin only)"""
        if current_user.user_type != 'Admin':
            return {'error': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)

        users = User.query.order_by(User.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return {
            'users': users_schema.dump(users.items),
            'total': users.total,
            'page': users.page,
            'per_page': users.per_page
        }


class AdminActivitiesResource(Resource):
    @login_required
    def get(self):
        """Get all activities (admin only)"""
        if current_user.user_type != 'Admin':
            return {'error': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)

        activities = ActivityLog.query \
            .join(User, ActivityLog.user_id == User.id) \
            .add_columns(User.username, User.user_type) \
            .order_by(ActivityLog.timestamp.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        # Format results
        results = []
        for activity, username, user_type in activities.items:
            result = activity_schema.dump(activity)
            result['username'] = username
            result['user_type'] = user_type
            results.append(result)

        return {
            'activities': results,
            'total': activities.total,
            'page': activities.page,
            'per_page': activities.per_page
        }


class AdminMetricsResource(Resource):
    @login_required
    def get(self):
        """Get system metrics (admin only)"""
        if current_user.user_type != 'Admin':
            return {'error': 'Unauthorized'}, 403

        # User statistics
        user_stats = db.session.query(
            User.user_type,
            db.func.count(User.id).label('count'),
            db.func.date(User.created_at).label('date')
        ).group_by(User.user_type, db.func.date(User.created_at)).all()

        # Activity statistics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        activity_stats = db.session.query(
            ActivityLog.activity_type,
            db.func.count(ActivityLog.id).label('count'),
            db.func.date(ActivityLog.timestamp).label('date')
        ).filter(ActivityLog.timestamp >= thirty_days_ago) \
            .group_by(ActivityLog.activity_type, db.func.date(ActivityLog.timestamp)) \
            .order_by(db.func.date(ActivityLog.timestamp).desc()).all()

        # Chat statistics (last 30 days)
        chat_stats = db.session.query(
            db.func.date(ActivityLog.timestamp).label('date'),
            db.func.count(ActivityLog.id).label('chat_count')
        ).filter(
            ActivityLog.timestamp >= thirty_days_ago,
            ActivityLog.activity_type == 'chat_message'
        ).group_by(db.func.date(ActivityLog.timestamp)) \
            .order_by(db.func.date(ActivityLog.timestamp).desc()).all()

        return {
            'user_statistics': [
                {'user_type': stat.user_type, 'count': stat.count, 'date': stat.date}
                for stat in user_stats
            ],
            'activity_statistics': [
                {'activity_type': stat.activity_type, 'count': stat.count, 'date': stat.date}
                for stat in activity_stats
            ],
            'chat_statistics': [
                {'date': stat.date, 'chat_count': stat.chat_count}
                for stat in chat_stats
            ],
            'system_metrics': metrics_tracker.get_system_metrics() if hasattr(metrics_tracker,
                                                                              'get_system_metrics') else {},
            'total_users': User.query.count(),
            'total_activities': ActivityLog.query.count()
        }


# ====================== API ROUTES ======================

# Authentication
api.add_resource(RegisterResource, '/api/register')
api.add_resource(LoginResource, '/api/login')
api.add_resource(LogoutResource, '/api/logout')
api.add_resource(ProfileResource, '/api/profile')

# Chat
api.add_resource(ChatResource, '/api/chat')
api.add_resource(FeedbackResource, '/api/feedback')

# User activities
api.add_resource(ActivityResource, '/api/activity')

# Search
api.add_resource(BookSearchResource, '/api/search/books')

# Admin endpoints
api.add_resource(AdminUsersResource, '/api/admin/users')
api.add_resource(AdminActivitiesResource, '/api/admin/activities')
api.add_resource(AdminMetricsResource, '/api/admin/metrics')


# ====================== ERROR HANDLERS ======================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ====================== INITIALIZE DATABASE ======================

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@library.com',
                first_name='System',
                last_name='Administrator',
                user_type='Admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin / admin123")


# ====================== MAIN ======================

if __name__ == '__main__':
    create_tables()

    print("""
    📚 Library Chatbot API with Flask-RESTful
    =========================================

    Available REST API Endpoints:

    🔐 Authentication:
      POST /api/register     - Register new user
      POST /api/login        - Login user
      POST /api/logout       - Logout user
      GET  /api/profile      - Get user profile

    💬 Chat:
      POST /api/chat         - Send chat message
      POST /api/feedback     - Submit feedback
      GET  /api/activity     - Get user activity

    🔍 Search:
      GET  /api/search/books - Search library catalog

    👑 Admin (Admin users only):
      GET  /api/admin/users      - Get all users
      GET  /api/admin/activities - Get all activities
      GET  /api/admin/metrics    - Get system metrics

    Running on http://127.0.0.1:5000
    """)

    app.run(host='0.0.0.0', port=5000, debug=True)