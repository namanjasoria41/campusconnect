from flask import render_template
from flask_login import login_required
from . import events_bp
from ..models import Event


@events_bp.route("/")
@login_required
def list_events():
    events = Event.query.order_by(Event.date.asc()).all()
    return render_template("events/events.html", events=events)
