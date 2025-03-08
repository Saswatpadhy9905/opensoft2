from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for

mail = Mail()  # Initialize Mail without app

def send_verification_email(user):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(user.email, salt='email-confirm')
    confirm_url = url_for('verify_email', token=token, _external=True)

    msg = Message('Confirm Your Email', sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.body = f'Click the link to verify your email: {confirm_url}'
    mail.send(msg)