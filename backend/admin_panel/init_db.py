from werkzeug.security import generate_password_hash
from app import app, db
from models import User
import uuid
import hashlib

def create_admin():
    with app.app_context():
        db.create_all()
        
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                id=str(uuid.uuid4()),
                name='admin',
                email='admin@example.com',
                password=hashlib.md5("password".encode()).hexdigest()
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin user created')
        else:
            print('Admin user already exists')

if __name__ == '__main__':
    create_admin()
