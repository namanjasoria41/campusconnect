from flask import Blueprint

swipe_bp = Blueprint("swipe", __name__, url_prefix="/swipe")

from . import routes  # noqa
