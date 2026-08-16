"""
routes/feedback_routes.py
---------------------------------------
Recommendation Feedback Routes
MoodFlix AI
"""

from flask import Blueprint, request, jsonify, g

from services import feedback_service
from utils.auth import login_required

feedback_routes = Blueprint("feedback_routes", __name__)


@feedback_routes.route("/api/feedback", methods=["POST"])
@login_required
def add_feedback():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    feedback, error = feedback_service.add_feedback(str(g.current_user["_id"]), data)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "message": "Thanks for the feedback!", "feedback": feedback})
