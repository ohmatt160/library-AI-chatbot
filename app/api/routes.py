"""
API routes for the Intelligent Library Chat Assistant
"""

from flask import Blueprint, request, jsonify, session, render_template
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.dialogue_manager import DialogueManager
from app.models.rule_engine import AdvancedRuleEngine
from app.models.nlp_engine import HybridNLPEngine
from app.models.response_generator import ResponseGenerator
from app.utils.database import db
from app.utils.metrics import MetricsTracker
import time
import uuid

# Initialize components
rule_engine = AdvancedRuleEngine('app/data/rules.json')
nlp_engine = HybridNLPEngine()
response_generator = ResponseGenerator('app/data/response_templates.json')
metrics_tracker = MetricsTracker()

# Create dialogue manager
dialogue_manager = DialogueManager(rule_engine, nlp_engine, response_generator)

# Create Blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """Main chat endpoint"""
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400

        user_message = data['message'].strip()
        session_id = data.get('session_id', str(uuid.uuid4()))

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Get user identity from JWT
        user_id = get_jwt_identity()

        # Start timing
        start_time = time.time()

        # Process message through dialogue manager
        result = dialogue_manager.process_message(
            user_id=user_id,
            session_id=session_id,
            message=user_message
        )

        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to ms

        # Track metrics
        metrics_tracker.record_interaction(
            user_id=user_id,
            session_id=session_id,
            message=user_message,
            response=result['response'],
            response_time=response_time,
            confidence=result['confidence'],
            method=result['processing_method']
        )

        # Prepare response
        response = {
            'response': result['response'],
            'session_id': session_id,
            'response_time_ms': round(response_time, 2),
            'confidence': round(result['confidence'], 3),
            'processing_method': result['processing_method'],
            'suggested_follow_ups': result.get('suggested_follow_ups', []),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@api_bp.route('/session/start', methods=['POST'])
@jwt_required()
def start_session():
    """Start a new chat session"""
    try:
        session_id = str(uuid.uuid4())
        user_id = get_jwt_identity()

        # Initialize session in dialogue manager
        dialogue_manager.initialize_session(user_id, session_id)

        # Record session start
        metrics_tracker.record_session_start(user_id, session_id)

        return jsonify({
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'message': 'Session started successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/search/books', methods=['GET'])
@jwt_required()
def search_books():
    """Search library catalog"""
    try:
        query = request.args.get('q', '')
        author = request.args.get('author', '')
        subject = request.args.get('subject', '')
        limit = int(request.args.get('limit', 20))

        if not query and not author and not subject:
            return jsonify({'error': 'At least one search parameter is required'}), 400

        # Use NLP to understand search intent
        nlp_result = nlp_engine.analyze(query if query else f"{author} {subject}")

        # Search database
        from app.utils.database import search_catalog
        results = search_catalog(
            query=query,
            author=author,
            subject=subject,
            limit=limit
        )

        return jsonify({
            'query': query,
            'intent': nlp_result.get('intent'),
            'count': len(results),
            'results': results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Submit feedback for a response"""
    try:
        data = request.get_json()

        required_fields = ['message_id', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Store feedback
        from app.utils.database import store_feedback
        feedback_id = store_feedback(
            message_id=data['message_id'],
            rating=data['rating'],
            comment=data.get('comment', ''),
            corrected_response=data.get('corrected_response', ''),
            user_id=get_jwt_identity()
        )

        # Update learning if correction provided
        if data['rating'] == 'thumbs_down' and data.get('corrected_response'):
            from app.models.feedback_module import update_knowledge_base
            update_knowledge_base(
                original_message_id=data['message_id'],
                corrected_response=data['corrected_response']
            )

        return jsonify({
            'status': 'success',
            'feedback_id': feedback_id,
            'message': 'Thank you for your feedback!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/metrics', methods=['GET'])
@jwt_required()
def get_metrics():
    """Get system metrics (admin only)"""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        # Add admin check logic here

        # Get metrics
        metrics = metrics_tracker.get_all_metrics()

        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from app.utils.database import check_db_connection
        db_ok = check_db_connection()

        # Check NLP models
        nlp_ok = nlp_engine.is_ready()

        status = 'healthy' if db_ok and nlp_ok else 'unhealthy'

        return jsonify({
            'status': status,
            'database': 'connected' if db_ok else 'disconnected',
            'nlp_models': 'loaded' if nlp_ok else 'not loaded',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Serve chat interface
@api_bp.route('/chat/interface')
def chat_interface():
    """Serve the chat interface"""
    return render_template('chat.html')