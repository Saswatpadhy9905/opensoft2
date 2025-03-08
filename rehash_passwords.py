from app import app, db, bcrypt
from models import User

with app.app_context():
    users = User.query.all()
    for user in users:
        if not user.password.startswith("$2b$"):  # Check if the password is not already bcrypt hashed
            hashed_password = bcrypt.generate_password_hash(user.password).decode('utf-8')
            user.password = hashed_password
            db.session.commit()