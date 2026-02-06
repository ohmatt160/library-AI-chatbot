from app.extensions import db
from app.model import Feedback, User
from sqlalchemy import text

def check_db_connection():
    """Check if the database connection is active"""
    try:
        # Use a simple query to verify connection
        db.session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

def store_feedback(message_id, rating, comment='', corrected_response='', user_id=None):
    """Store user feedback in the database"""
    try:
        feedback = Feedback(
            message_id=message_id,
            rating=rating,
            comment=comment,
            corrected_response=corrected_response,
            user_id=user_id
        )
        db.session.add(feedback)
        db.session.commit()
        return feedback.id
    except Exception as e:
        print(f"Error storing feedback: {e}")
        db.session.rollback()
        return None

def search_catalog(query='', author='', subject='', limit=20):
    """
    Search the local book catalog.
    Currently returns an empty list as a placeholder for local search logic.
    """
    # In a real implementation, this would query a Books table
    return []

def get_user_activity(user_id, limit=50):
    """Get recent activity for a specific user"""
    from app.model import ActivityLog
    return ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
