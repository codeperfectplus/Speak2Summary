# cython: language_level=3
from flask import render_template

from . import audio_bp


# Error handler for 404
@audio_bp.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@audio_bp.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

@audio_bp.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@audio_bp.errorhandler(400)
def bad_request(e):
    return render_template("400.html"), 400

@audio_bp.errorhandler(405)
def method_not_allowed(e):
    return render_template("405.html"), 405