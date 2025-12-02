from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import swipe_bp
from ..models import User, Like, Match
from ..subscriptions import get_plan
from ..extensions import db


@swipe_bp.route("/")
@login_required
def swipe_view():
    # Very simple: show the first other user
    candidate = User.query.filter(User.id != current_user.id).first()
    return render_template("swipe/swipe.html", candidate=candidate)


@swipe_bp.route("/like/<int:user_id>")
@login_required
def like_user(user_id):
    plan = get_plan(current_user.plan or "free")
    limit = plan["swipes_per_day"]

    if not current_user.can_swipe_today(limit):
        flash("You reached your daily swipe limit. Upgrade your plan!", "warning")
        return redirect(url_for("billing.pricing"))

    # register swipe
    current_user.register_swipe()

    other = User.query.get_or_404(user_id)
    like = Like(from_user_id=current_user.id, to_user_id=other.id, mode="dating")
    db.session.add(like)
    db.session.commit()

    # check reverse like for match
    reverse = Like.query.filter_by(from_user_id=other.id, to_user_id=current_user.id, mode="dating").first()
    if reverse:
        match = Match(user1_id=current_user.id, user2_id=other.id, mode="dating")
        db.session.add(match)
        db.session.commit()
        flash("It's a match! You can now chat.", "success")
        return redirect(url_for("chat.matches"))

    flash("Liked!", "info")
    return redirect(url_for("swipe.swipe_view"))
