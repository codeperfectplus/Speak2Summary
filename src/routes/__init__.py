from flask import Blueprint

audio_bp = Blueprint('audio', __name__)

# Import route modules to register routes to the blueprint
from . import (
    api_routes,
    upload_routes,
    status_routes,
    view_routes,
    delete_routes,
    health_routes,
    home_routes,
    mindmap_route
)
