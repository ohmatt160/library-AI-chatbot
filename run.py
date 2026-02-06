from app import create_app
from app.extensions import db
from app.model import User

app = create_app()

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

if __name__ == '__main__':
    create_tables()

    print("""
    📚 Library Chatbot API with Flask-RESTful
    =========================================
    Running on http://0.0.0.0:5000
    """)

    app.run(host='0.0.0.0', port=5000, debug=True)
