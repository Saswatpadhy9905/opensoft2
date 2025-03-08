from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt  # Use flask_bcrypt for password hashing
from itsdangerous import URLSafeTimedSerializer
from forms import RegistrationForm, LoginForm
from config import Config  # Import configuration from config.py

app = Flask(__name__)
app.config.from_object(Config)  # Set configuration from Config class

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
bcrypt = Bcrypt(app)  # Initialize Bcrypt for password hashing
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Email Verification Serializer
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

# Load User for Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(email=form.email.data, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        token = serializer.dumps(new_user.email, salt="email-confirm")
        verify_url = url_for("verify_email", token=token, _external=True)
        msg = Message("Verify Your Email", sender=app.config["MAIL_USERNAME"], recipients=[new_user.email])
        msg.body = f"Click the link to verify your email: {verify_url}"
        mail.send(msg)

        flash("A verification email has been sent!", "info")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

# Email Verification Route
@app.route("/verify_email/<token>")
def verify_email(token):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_verified = True
            db.session.commit()
            flash("Email verified successfully! You can now log in.", "success")
        else:
            flash("Invalid or expired token.", "danger")
    except:
        flash("Invalid or expired token.", "danger")

    return redirect(url_for("login"))

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if not user.is_verified:
                flash("Please verify your email first.", "warning")
                return redirect(url_for("login"))

            login_user(user)
            return redirect(url_for("profile"))

        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)

# Profile Page (After Login)
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)

# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# Admin Page (Only for Admins)
@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash("Access denied! You are not an admin.", "danger")
        return redirect(url_for("home"))
    
    users = User.query.all()
    return render_template("admin.html", users=users)

# Run the App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure database is created
    app.run(debug=True)