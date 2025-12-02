import os
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import stories_bp
from ..extensions import db
from ..models import Story


@stories_bp.route("/upload", methods=["POST"])
@login_required
def upload_story():
    file = request.files.get("media")
    if not file:
        flash("No file selected.", "danger")
        return redirect(url_for("main.feed"))

    filename = f"story_{current_user.id}_{file.filename}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    story = Story(
        user_id=current_user.id,
        media=filename,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.session.add(story)
    db.session.commit()

    flash("Story uploaded!", "success")
    return redirect(url_for("main.feed"))


@stories_bp.route("/view/<int:user_id>")
@login_required
def view_story(user_id):
    stories = Story.query.filter(
        Story.user_id == user_id,
        Story.expires_at > datetime.utcnow()
    ).order_by(Story.created_at.asc()).all()

    story_urls = [
        url_for("static", filename="uploads/" + s.media)
        for s in stories
    ]

    return render_template(
        "stories/view.html",
        stories=stories,
        story_urls=story_urls
    )
