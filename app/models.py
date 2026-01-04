from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

# -------------------------------------------------
# Association table for Post <-> Hashtag (many-to-many)
# -------------------------------------------------
post_hashtags = db.Table(
    "post_hashtags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("hashtag_id", db.Integer, db.ForeignKey("hashtag.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    year = db.Column(db.String(20))
    branch = db.Column(db.String(50))
    bio = db.Column(db.Text)
    interests = db.Column(db.String(255))       # "hackathons,dance"
    looking_for = db.Column(db.String(255))     # "events,dating"
    photo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)

    # Relationships
    stories = db.relationship("Story", backref="author", lazy=True)
    gossips = db.relationship(
        "Gossip",
        foreign_keys="Gossip.created_by_user_id",
        backref="creator",
        lazy=True,
    )
    posts = db.relationship("Post", backref="author", lazy=True)

    # Subscription fields
    plan = db.Column(db.String(20), default="free")  # free / plus / pro
    plan_expires_at = db.Column(db.DateTime, nullable=True)

    # Swipe tracking
    last_swipe_date = db.Column(db.Date, nullable=True)
    swipes_today = db.Column(db.Integer, default=0)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_premium(self) -> bool:
        if self.plan in ("plus", "pro"):
            if self.plan_expires_at is None:
                return True
            return self.plan_expires_at > datetime.utcnow()
        return False

    def has_plan(self, required_plan: str) -> bool:
        order = {"free": 0, "plus": 1, "pro": 2}
        current = order.get(self.plan or "free", 0)
        req = order.get(required_plan, 0)

        if self.plan_expires_at and self.plan_expires_at <= datetime.utcnow():
            return required_plan == "free"

        return current >= req

    def can_swipe_today(self, max_swipes: int | None) -> bool:
        today = date.today()
        if self.last_swipe_date != today:
            self.last_swipe_date = today
            self.swipes_today = 0
        if max_swipes is None:
            return True
        return self.swipes_today < max_swipes

    def register_swipe(self):
        from .extensions import db as _db
        today = date.today()
        if self.last_swipe_date != today:
            self.last_swipe_date = today
            self.swipes_today = 0
        self.swipes_today += 1
        _db.session.commit()


class Post(db.Model):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(50), default="general")  # general/event/partner_request
    text = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # "general" | "announcement" | "event_promo" etc.
    is_featured = db.Column(db.Boolean, default=False)

    # Many-to-many with hashtags
    hashtags = db.relationship(
        "Hashtag",
        secondary=post_hashtags,
        back_populates="posts",
        lazy="subquery",
    )


class Hashtag(db.Model):
    __tablename__ = "hashtag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True, nullable=False)
    count = db.Column(db.Integer, default=0)  # Track hashtag usage count

    posts = db.relationship(
        "Post",
        secondary=post_hashtags,
        back_populates="hashtags",
    )


class Event(db.Model):
    __tablename__ = "event"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))  # tech/cultural/sports
    date = db.Column(db.DateTime)
    location = db.Column(db.String(120))
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))  # Track event creator
    is_official = db.Column(db.Boolean, default=False)  # admin posted
    highlight = db.Column(db.Boolean, default=False)    # show banner

    partner_posts = db.relationship("EventPartnerPost", backref="event", lazy=True)
    posts = db.relationship("Post", backref="event_ref", lazy=True)


class EventPartnerPost(db.Model):
    __tablename__ = "event_partner_post"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    role = db.Column(db.String(100))
    skill_level = db.Column(db.String(50))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Like(db.Model):
    __tablename__ = "like"

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    mode = db.Column(db.String(20))      # "dating" or "event"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Match(db.Model):
    __tablename__ = "match"

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    mode = db.Column(db.String(20))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("Message", backref="match", lazy=True)


class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Story(db.Model):
    __tablename__ = "story"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    media = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)


class Gossip(db.Model):
    __tablename__ = "gossip"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))   # e.g. hostel, crush, fest, prof, placement
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_featured = db.Column(db.Boolean, default=False)

    # We keep creator internally for moderation, but never show name in UI
    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )

    # Votes
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

    # Soft delete (for admin moderation)
    is_deleted = db.Column(db.Boolean, default=False)

    comments = db.relationship("GossipComment", backref="gossip", lazy=True)
    votes = db.relationship(
        "GossipVote",
        backref="gossip",
        lazy=True,
        cascade="all, delete-orphan",
    )


class GossipComment(db.Model):
    __tablename__ = "gossip_comment"

    id = db.Column(db.Integer, primary_key=True)
    gossip_id = db.Column(db.Integer, db.ForeignKey("gossip.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Internal only; UI remains anonymous
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class GossipVote(db.Model):
    """
    Tracks one vote (up or down) per user per gossip.
    value: +1 = upvote, -1 = downvote
    """
    __tablename__ = "gossip_vote"

    id = db.Column(db.Integer, primary_key=True)
    gossip_id = db.Column(db.Integer, db.ForeignKey("gossip.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    value = db.Column(db.Integer, nullable=False)  # +1 or -1

    __table_args__ = (
        db.UniqueConstraint("gossip_id", "user_id", name="uq_gossip_vote"),
    )


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    gossip_id = db.Column(db.Integer, db.ForeignKey('gossip.id'), nullable=True)

    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resolved = db.Column(db.Boolean, default=False)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


