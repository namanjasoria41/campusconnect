from datetime import datetime, timedelta
from .extensions import db

PLANS = {
    "free": {
        "name": "Free",
        "price_inr": 0,
        "swipes_per_day": 20,
        "see_likes": False,
        "unlimited_swipes": False,
    },
    "plus": {
        "name": "Plus",
        "price_inr": 99,
        "swipes_per_day": 100,
        "see_likes": True,
        "unlimited_swipes": False,
    },
    "pro": {
        "name": "Pro",
        "price_inr": 199,
        "swipes_per_day": None,  # unlimited
        "see_likes": True,
        "unlimited_swipes": True,
    },
}


def get_plan(plan_key: str):
    return PLANS.get(plan_key)


def plan_duration_days() -> int:
    return 30


def apply_plan(user, plan_key: str):
    user.plan = plan_key
    if plan_key == "free":
        user.plan_expires_at = None
    else:
        user.plan_expires_at = datetime.utcnow() + timedelta(days=plan_duration_days())
    db.session.commit()
