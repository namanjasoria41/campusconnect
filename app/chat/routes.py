from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from . import chat_bp
from ..models import Match, Message, User
from ..extensions import db


@chat_bp.route("/")
@login_required
def matches():
    matches = Match.query.filter(
        (Match.user1_id == current_user.id) | (Match.user2_id == current_user.id)
    ).order_by(Match.created_at.desc()).all()
    return render_template("chat/matches.html", matches=matches)


@chat_bp.route("/room/<int:match_id>", methods=["GET", "POST"])
@login_required
def chat_room(match_id):
    match = Match.query.get_or_404(match_id)
    if current_user.id not in (match.user1_id, match.user2_id):
        flash("Not allowed.", "danger")
        return redirect(url_for("chat.matches"))

    if request.method == "POST":
        text = request.form.get("text")
        if text:
            msg = Message(match_id=match.id, sender_id=current_user.id, text=text)
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for("chat.chat_room", match_id=match.id))

    messages = Message.query.filter_by(match_id=match.id).order_by(Message.created_at.asc()).all()
    other_id = match.user1_id if match.user2_id == current_user.id else match.user2_id
    other = User.query.get(other_id)
    return render_template("chat/chat.html", match=match, other=other, messages=messages)
