from app.extensions import db
from app.model import Feedback, User, Book, Contact
from sqlalchemy import text, or_

def check_db_connection():
    """Check if the database connection is active"""
    try:
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
    """
    try:
        q = Book.query
        if query:
            q = q.filter(or_(
                Book.title.ilike(f'%{query}%'),
                Book.author.ilike(f'%{query}%'),
                Book.topic.ilike(f'%{query}%'),
                Book.isbn.ilike(f'%{query}%')
            ))
        if author:
            q = q.filter(Book.author.ilike(f'%{author}%'))
        if subject:
            q = q.filter(Book.topic.ilike(f'%{subject}%'))

        results = q.limit(limit).all()
        return [
            {
                'title': b.title,
                'author': b.author,
                'isbn': b.isbn,
                'copies_available': b.copies_available,
                'location': b.location,
                'summary': b.summary,
                'id': b.id
            } for b in results
        ]
    except Exception as e:
        print(f"Error searching catalog: {e}")
        return []

def get_contact_info(department=None):
    """Get library contact information"""
    try:
        q = Contact.query
        if department:
            q = q.filter(Contact.department.ilike(f'%{department}%'))
        results = q.all()
        return [
            {
                'department': c.department,
                'phone': c.phone,
                'email': c.email,
                'hours': c.hours
            } for c in results
        ]
    except Exception as e:
        print(f"Error getting contact info: {e}")
        return []

def get_user_account(user_id):
    """Get user account details including borrowed books"""
    try:
        user = User.query.get(user_id)
        if user:
            return {
                'username': user.username,
                'borrowed_books': user.borrowed_books,
                'user_type': user.user_type
            }
        return None
    except Exception as e:
        print(f"Error getting user account: {e}")
        return None

def get_user_activity(user_id, limit=50):
    """Get recent activity for a specific user"""
    from app.model import ActivityLog
    return ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
