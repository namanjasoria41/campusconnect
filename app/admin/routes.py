from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy import func

from . import admin_bp
from ..extensions import db
from ..models import User, Post, Gossip, Report, Event


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not getattr(current_user, "is_admin", False):
            flash("Admin access only.", "danger")
            return redirect(url_for("main.feed"))
        return f(*args, **kwargs)
    return wrapper


# DASHBOARD
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    post_count = Post.query.count()
    gossip_count = Gossip.query.count()
    report_open_count = Report.query.filter_by(resolved=False).count()
    event_count = Event.query.count()

    # Simple analytics: last 7 days posts
    post_stats = (
        db.session.query(
            func.date(Post.created_at).label("day"),
            func.count(Post.id)
        )
        .group_by(func.date(Post.created_at))
        .order_by(func.date(Post.created_at).desc())
        .limit(7)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        user_count=user_count,
        post_count=post_count,
        gossip_count=gossip_count,
        report_open_count=report_open_count,
        event_count=event_count,
        post_stats=post_stats,
    )


# USERS MANAGEMENT
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/ban_user/<int:user_id>")
@login_required
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Cannot ban another admin.", "danger")
        return redirect(url_for("admin.users"))
    user.is_banned = True
    db.session.commit()
    flash("User banned.", "warning")
    return redirect(url_for("admin.users"))


@admin_bp.route("/unban_user/<int:user_id>")
@login_required
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    flash("User unbanned.", "success")
    return redirect(url_for("admin.users"))


# POSTS MANAGEMENT
@admin_bp.route("/posts")
@login_required
@admin_required
def posts():
    posts = Post.query.order_by(Post.created_at.desc()).limit(100).all()
    return render_template("admin/posts.html", posts=posts)


@admin_bp.route("/posts/delete/<int:post_id>")
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "success")
    return redirect(url_for("admin.posts"))


@admin_bp.route("/posts/feature/<int:post_id>")
@login_required
@admin_required
def feature_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_featured = True
    db.session.commit()
    flash("Post marked as featured.", "success")
    return redirect(url_for("admin.posts"))


@admin_bp.route("/posts/unfeature/<int:post_id>")
@login_required
@admin_required
def unfeature_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_featured = False
    db.session.commit()
    flash("Post unfeatured.", "success")
    return redirect(url_for("admin.posts"))


# GOSSIPS MANAGEMENT
@admin_bp.route("/gossips")
@login_required
@admin_required
def gossips():
    gossips = Gossip.query.order_by(Gossip.created_at.desc()).limit(100).all()
    return render_template("admin/gossips.html", gossips=gossips)


@admin_bp.route("/gossips/delete/<int:gossip_id>")
@login_required
@admin_required
def delete_gossip(gossip_id):
    gossip = Gossip.query.get_or_404(gossip_id)
    gossip.is_deleted = True
    db.session.commit()
    flash("Gossip marked as deleted.", "success")
    return redirect(url_for("admin.gossips"))


@admin_bp.route("/gossips/feature/<int:gossip_id>")
@login_required
@admin_required
def feature_gossip(gossip_id):
    gossip = Gossip.query.get_or_404(gossip_id)
    gossip.is_featured = True
    db.session.commit()
    flash("Gossip marked as featured.", "success")
    return redirect(url_for("admin.gossips"))


@admin_bp.route("/gossips/unfeature/<int:gossip_id>")
@login_required
@admin_required
def unfeature_gossip(gossip_id):
    gossip = Gossip.query.get_or_404(gossip_id)
    gossip.is_featured = False
    db.session.commit()
    flash("Gossip unfeatured.", "success")
    return redirect(url_for("admin.gossips"))


# REPORTS REVIEW
@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("admin/reports.html", reports=reports)


@admin_bp.route("/reports/resolve/<int:report_id>")
@login_required
@admin_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.resolved = True
    report.resolved_by_id = current_user.id
    db.session.commit()
    flash("Report marked as resolved.", "success")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/reports/delete_post/<int:report_id>")
@login_required
@admin_required
def reports_delete_post(report_id):
    report = Report.query.get_or_404(report_id)
    if report.post_id:
        post = Post.query.get(report.post_id)
        if post:
            db.session.delete(post)
    report.resolved = True
    report.resolved_by_id = current_user.id
    db.session.commit()
    flash("Post deleted and report resolved.", "success")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/reports/delete_gossip/<int:report_id>")
@login_required
@admin_required
def reports_delete_gossip(report_id):
    report = Report.query.get_or_404(report_id)
    if report.gossip_id:
        gossip = Gossip.query.get(report.gossip_id)
        if gossip:
            gossip.is_deleted = True
    report.resolved = True
    report.resolved_by_id = current_user.id
    db.session.commit()
    flash("Gossip removed and report resolved.", "success")
    return redirect(url_for("admin.reports"))


# EVENTS (ADMIN ONLY)
@admin_bp.route("/events/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_event():
    from datetime import datetime
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        date_str = request.form.get("date")
        location = request.form.get("location")

        if not title or not date_str:
            flash("Title and date are required.", "danger")
            return redirect(url_for("admin.create_event"))

        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for("admin.create_event"))

        event = Event(
            title=title,
            description=description,
            date=dt,
            location=location,
            created_by_id=current_user.id,
            is_official=True,
            highlight=True,
        )
        db.session.add(event)
        db.session.commit()
        flash("Official event created.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/create_event.html")


# ANNOUNCEMENTS (SPECIAL POSTS)
@admin_bp.route("/announcements/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_announcement():
    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            flash("Announcement cannot be empty.", "danger")
            return redirect(url_for("admin.create_announcement"))

        post = Post(
            user_id=current_user.id,
            text=text,
            type="announcement",
            is_featured=True
        )
        db.session.add(post)
        db.session.commit()
        flash("Announcement posted and featured.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/create_announcement.html")
