import uuid
import time
from datetime import datetime, timedelta
from flask import request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_restful import Resource
from app.extensions import db, login_manager
from app.model import ActivityLog, User, register_parser, user_schema, login_parser, UserSession, chat_parser, \
    feedback_parser, Feedback, activities_schema, search_parser, users_schema, activity_schema
from app.chatbot import dialogue_manager, metrics_tracker, opac_client

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

class GetSession(Resource):
    def get(self):
        """Get or create a session"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        return jsonify({
            'session_id': session['session_id'],
            'user_authenticated': current_user.is_authenticated
        })

class RegisterResource(Resource):
    def post(self):
        """Register a new user"""
        args = register_parser.parse_args()

        if User.query.filter_by(username=args['username']).first():
            return {'error': 'Username already exists'}, 400

        if User.query.filter_by(email=args['email']).first():
            return {'error': 'Email already exists'}, 400

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

        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user)

        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        client_info = get_client_info()
        user_session = UserSession(
            user_id=user.id,
            session_id=session['session_id'],
            **client_info
        )
        db.session.add(user_session)
        db.session.commit()

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
        log_activity(current_user.id, session.get('session_id'), 'logout', {})

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

        session_id = args.get('session_id') or session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

        user_id = current_user.id if current_user.is_authenticated else f"anon_{session_id}"
        start_time = time.time()

        try:
            result = dialogue_manager.process_message(
                user_id=user_id,
                session_id=session_id,
                message=args['message']
            )

            required_keys = ['response', 'confidence', 'processing_method']
            for key in required_keys:
                if key not in result:
                    raise KeyError(f"Missing required key in result: {key}")

            if not isinstance(result['response'], str):
                result['response'] = str(result['response'])

            if not result['response']:
                result['response'] = "I'm here to help with library services."

            if not isinstance(result['confidence'], (int, float)):
                result['confidence'] = 0.0
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': 'Processing error', 'message': str(e)}, 500

        response_time = (time.time() - start_time) * 1000

        if current_user.is_authenticated:
            log_activity(current_user.id, session_id, 'chat_message', {
                'message': args['message'],
                'response_time_ms': response_time,
                'confidence': result.get('confidence', 0),
                'intent': result.get('intent', 'unknown')
            })

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
    def post(self):
        """Submit feedback"""
        args = feedback_parser.parse_args()

        feedback = Feedback(
            user_id=current_user.id if current_user.is_authenticated else None,
            message_id=args['message_id'],
            rating=args['rating'],
            comment=args.get('comment', ''),
            corrected_response=args.get('corrected_response', '')
        )

        db.session.add(feedback)
        db.session.commit()

        if current_user.is_authenticated:
            log_activity(current_user.id, session.get('session_id'), 'feedback', {
                'message_id': args['message_id'],
                'rating': args['rating']
            })

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
    def get(self):
        """Search books"""
        args = search_parser.parse_args()

        if current_user.is_authenticated:
            log_activity(current_user.id, session.get('session_id'), 'book_search', {
                'query': args['q'],
                'author': args.get('author'),
                'subject': args.get('subject')
            })

        local_results = []
        opac_results = opac_client.search(args['q'], args.get('author'), args.get('subject'))
        results = local_results + opac_results

        return {
            'query': args['q'],
            'count': len(results),
            'results': results[:20],
            'source': 'local+opac'
        }

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

        user_stats = db.session.query(
            User.user_type,
            db.func.count(User.id).label('count'),
            db.func.date(User.created_at).label('date')
        ).group_by(User.user_type, db.func.date(User.created_at)).all()

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        activity_stats = db.session.query(
            ActivityLog.activity_type,
            db.func.count(ActivityLog.id).label('count'),
            db.func.date(ActivityLog.timestamp).label('date')
        ).filter(ActivityLog.timestamp >= thirty_days_ago) \
            .group_by(ActivityLog.activity_type, db.func.date(ActivityLog.timestamp)) \
            .order_by(db.func.date(ActivityLog.timestamp).desc()).all()

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
                {'user_type': stat.user_type, 'count': stat.count, 'date': str(stat.date)}
                for stat in user_stats
            ],
            'activity_statistics': [
                {'activity_type': stat.activity_type, 'count': stat.count, 'date': str(stat.date)}
                for stat in activity_stats
            ],
            'chat_statistics': [
                {'date': str(stat.date), 'chat_count': stat.chat_count}
                for stat in chat_stats
            ],
            'system_metrics': metrics_tracker.get_all_metrics(),
            'total_users': User.query.count(),
            'total_activities': ActivityLog.query.count()
        }
