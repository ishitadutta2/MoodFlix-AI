"""
routes/password_reset_routes.py
---------------------------------------
Password Reset Routes
MoodFlix AI
"""

from flask import Blueprint, request, jsonify, render_template

from services import account_service
from extensions import limiter

password_reset_routes = Blueprint("password_reset_routes", __name__)


# -----------------------------------
# Pages
# -----------------------------------
@password_reset_routes.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@password_reset_routes.route("/reset-password")
def reset_password_page():
    token = request.args.get("token", "")
    return render_template("reset_password.html", token=token)


# -----------------------------------
# API
# -----------------------------------
@password_reset_routes.route("/api/forgot-password", methods=["POST"])
@limiter.limit("5 per minute")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip()

    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400

    account_service.request_password_reset(email, request.host_url)

    # Deliberately generic — don't reveal whether the email exists.
    return jsonify({
        "success": True,
        "message": "If an account exists for that email, we've sent a reset link."
    })


@password_reset_routes.route("/api/reset-password", methods=["POST"])
@limiter.limit("10 per minute")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    new_password = data.get("new_password", "")

    if not token:
        return jsonify({"success": False, "message": "Missing reset token."}), 400

    ok, error = account_service.reset_password(token, new_password)
    if not ok:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "message": "Password reset. You can now log in."})
