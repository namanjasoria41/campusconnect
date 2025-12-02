import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import razorpay

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Razorpay client (reads from env; replace with your test keys)
razorpay_client = razorpay.Client(auth=(
    os.environ.get("RAZORPAY_KEY_ID", "rzp_test_yourkeyid"),
    os.environ.get("RAZORPAY_KEY_SECRET", "yourkeysecret")
))
