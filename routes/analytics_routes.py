"""
routes/analytics_routes.py
---------------------------------------
Analytics Routes
MoodFlix AI
"""

from flask import Blueprint, jsonify, g

from services import analytics_service
from utils.auth import login_required

analytics_routes = Blueprint("analytics_routes", __name__)


@analytics_routes.route("/api/analytics", methods=["GET"])
@login_required
def get_analytics():
    data = analytics_service.get_analytics(str(g.current_user["_id"]))
    return jsonify({"success": True, "analytics": data})
