"""
routes/profile_routes.py
---------------------------------------
Profile Routes
MoodFlix AI

Thin controllers only — logic lives in services/profile_service.py.
"""

from flask import Blueprint, request, jsonify, g, session, current_app

from database.user_model import public_user
from services import profile_service
from utils.auth import login_required

profile_routes = Blueprint("profile_routes", __name__)


@profile_routes.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    return jsonify({"success": True, "profile": public_user(g.current_user)})


@profile_routes.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    profile, error = profile_service.update_profile(g.current_user, data)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "message": "Profile updated successfully.", "profile": profile})


@profile_routes.route("/api/profile/avatar", methods=["POST"])
@login_required
def update_avatar():
    file = request.files.get("avatar")
    upload_root = current_app.config.get("UPLOAD_FOLDER") or "static/uploads"
    if not upload_root.startswith("/"):
        upload_root = f"{current_app.root_path}/{upload_root}"

    avatar_url, error = profile_service.update_avatar(g.current_user, file, upload_root)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "message": "Profile picture updated.", "avatar": avatar_url})


@profile_routes.route("/api/profile/password", methods=["PUT"])
@login_required
def change_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    ok, error = profile_service.change_password(
        g.current_user, data.get("current_password", ""), data.get("new_password", "")
    )
    if not ok:
        status = 401 if error == "Current password is incorrect." else 400
        return jsonify({"success": False, "message": error}), status

    return jsonify({"success": True, "message": "Password changed successfully."})


@profile_routes.route("/api/profile", methods=["DELETE"])
@login_required
def delete_account():
    profile_service.delete_account(g.current_user)
    session.clear()
    return jsonify({"success": True, "message": "Account deleted successfully."})


@profile_routes.route("/api/profile/stats", methods=["GET"])
@login_required
def profile_stats():
    return jsonify({"success": True, "stats": profile_service.get_stats(g.current_user)})
