from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import main_bp
from ..models import Post, Hashtag, Story, User
from ..extensions import db
from datetime import datetime


@main_bp.route("/", methods=["GET", "POST"])
@login_required
def feed():
    # Handle POST request - create new post
    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            flash("Post cannot be empty.", "danger")
        else:
            post = Post(user_id=current_user.id, text=text, type="general")
            db.session.add(post)
            db.session.commit()
            flash("Post created.", "success")
            return redirect(url_for("main.feed"))

    # Handle GET request - display feed
    now = datetime.utcnow()

    # Fetch active stories
    my_story = Story.query.filter(
        Story.user_id == current_user.id,
        Story.expires_at > now
    ).order_by(Story.created_at.desc()).first()

    story_users = (
        db.session.query(User)
        .join(Story, Story.user_id == User.id)
        .filter(
            Story.expires_at > now,
            User.id != current_user.id
        )
        .distinct()
        .all()
    )

    # Fetch posts and trending hashtags
    posts = Post.query.order_by(Post.created_at.desc()).all()
    trending = Hashtag.query.order_by(Hashtag.count.desc()).limit(10).all()

    return render_template(
        "main/feed.html",
        posts=posts,
        trending=trending,
        my_story=my_story,
        story_users=story_users,
    )

