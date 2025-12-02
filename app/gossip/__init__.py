from flask import Blueprint

gossip_bp = Blueprint("gossip", __name__, url_prefix="/gossip")

from . import routes  # noqa
