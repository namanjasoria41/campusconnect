from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from . import gossip_bp
from ..extensions import db
from ..models import Gossip, GossipComment, GossipVote


# Available gossip categories for filters and dropdown
CATEGORIES = [
    "hostel",
    "crush",
    "fest",
    "professors",
    "placements",
    "random",
]


@gossip_bp.route("/", methods=["GET", "POST"])
@login_required
def feed():
    """
    Anonymous gossip feed:
    - POST: create a new anonymous gossip
    - GET: list gossips with category + sort filters
    """

    # ---------- CREATE NEW GOSSIP ----------
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        category = request.form.get("category", "random")

        if not text:
            flash("Gossip cannot be empty.", "danger")
            return redirect(url_for("gossip.feed"))

        # Basic sanity: unknown categories fall back to 'random'
        if category not in CATEGORIES:
            category = "random"

        gossip = Gossip(
            text=text,
            category=category,
            created_by_user_id=current_user.id,
        )
        db.session.add(gossip)
        db.session.commit()
        flash("Anonymous gossip posted 👀", "success")
        return redirect(url_for("gossip.feed"))

    # ---------- LIST / FILTER GOSSIPS ----------
    # Query params: ?category=hostel&sort=top
    category_filter = request.args.get("category", "all")
    sort = request.args.get("sort", "top")  # "top" | "new"

    query = Gossip.query.filter_by(is_deleted=False)

    # Filter by category if not "all"
    if category_filter != "all":
        query = query.filter_by(category=category_filter)

    # Sorting mode
    if sort == "new":
        query = query.order_by(Gossip.created_at.desc())
    else:
        # "top" = highest score (upvotes - downvotes), tie-break by newest
        query = query.order_by(
            (Gossip.upvotes - Gossip.downvotes).desc(),
            Gossip.created_at.desc(),
        )

    gossips = query.all()

    return render_template(
        "gossip/feed.html",
        gossips=gossips,
        categories=CATEGORIES,
        current_category=category_filter,
        current_sort=sort,
    )


@gossip_bp.route("/<int:gossip_id>", methods=["GET", "POST"])
@login_required
def detail(gossip_id):
    """
    Gossip detail page:
    - GET: show one gossip + comments
    - POST: add anonymous comment
    """
    gossip = Gossip.query.get_or_404(gossip_id)
    if gossip.is_deleted:
        flash("This gossip has been removed.", "warning")
        return redirect(url_for("gossip.feed"))

    # ---------- ADD COMMENT ----------
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Comment cannot be empty.", "danger")
        else:
            comment = GossipComment(
                gossip_id=gossip.id,
                text=text,
                created_by_user_id=current_user.id,
            )
            db.session.add(comment)
            db.session.commit()
            flash("Comment added anonymously.", "success")

        return redirect(url_for("gossip.detail", gossip_id=gossip.id))

    # ---------- LOAD COMMENTS ----------
    comments = (
        GossipComment.query.filter_by(gossip_id=gossip.id)
        .order_by(GossipComment.created_at.asc())
        .all()
    )

    # Current user's vote (for highlighting in template if you want)
    vote = GossipVote.query.filter_by(
        gossip_id=gossip.id,
        user_id=current_user.id,
    ).first()
    user_vote = vote.value if vote else 0

    return render_template(
        "gossip/detail.html",
        gossip=gossip,
        comments=comments,
        user_vote=user_vote,
    )


@gossip_bp.route("/vote/<int:gossip_id>", methods=["POST"])
@login_required
def vote(gossip_id):
    """
    AJAX endpoint to upvote/downvote a gossip.
    - action = "up" -> +1
    - action = "down" -> -1
    - clicking the same vote again removes the vote
    """
    gossip = Gossip.query.get_or_404(gossip_id)
    if gossip.is_deleted:
        return jsonify({"ok": False, "error": "Gossip removed"}), 400

    action = request.form.get("action")  # "up" or "down"
    if action not in ("up", "down"):
        return jsonify({"ok": False, "error": "Invalid action"}), 400

    value = 1 if action == "up" else -1

    vote = GossipVote.query.filter_by(
        gossip_id=gossip.id,
        user_id=current_user.id,
    ).first()

    # Remove previous influence, if any
    if vote:
        if vote.value == 1:
            gossip.upvotes -= 1
        elif vote.value == -1:
            gossip.downvotes -= 1

        # Same vote clicked again -> remove vote entirely
        if vote.value == value:
            db.session.delete(vote)
            db.session.commit()
            score = gossip.upvotes - gossip.downvotes
            return jsonify(
                {
                    "ok": True,
                    "upvotes": gossip.upvotes,
                    "downvotes": gossip.downvotes,
                    "score": score,
                    "user_vote": 0,
                }
            )

        # Switch vote
        vote.value = value
    else:
        # First-time vote by this user on this gossip
        vote = GossipVote(
            gossip_id=gossip.id,
            user_id=current_user.id,
            value=value,
        )
        db.session.add(vote)

    # Apply new influence
    if value == 1:
        gossip.upvotes += 1
    else:
        gossip.downvotes += 1

    db.session.commit()

    score = gossip.upvotes - gossip.downvotes

    return jsonify(
        {
            "ok": True,
            "upvotes": gossip.upvotes,
            "downvotes": gossip.downvotes,
            "score": score,
            "user_vote": value,
        }
    )
