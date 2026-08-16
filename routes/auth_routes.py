"""
routes/auth_routes.py
-----------------------------------
Authentication Routes
MoodFlix AI

Thin controllers only — logic lives in services/user_service.py.
"""

from flask import Blueprint, request, jsonify, session

from database.user_model import public_user
from services import user_service, account_service
from extensions import limiter
from utils.logger import get_logger

log = get_logger("auth_routes")

auth_routes = Blueprint("auth_routes", __name__)


# -----------------------------------
# Login
# -----------------------------------
@auth_routes.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    user, error, status = user_service.login_user(data.get("email", ""), data.get("password", ""))

    if error:
        return jsonify({"success": False, "message": error}), status

    session.permanent = True
    session["user_id"] = str(user.get("_id"))
    session["user"] = user.get("email")
    session["remember_me"] = bool(data.get("remember_me"))

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": public_user(user),
    })


# -----------------------------------
# Signup
# -----------------------------------
@auth_routes.route("/api/signup", methods=["POST"])
@limiter.limit("10 per minute")
def signup():

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    user, error, status = user_service.register_user(
        data.get("name", ""), data.get("email", ""), data.get("password", "")
    )

    if error:
        return jsonify({"success": False, "message": error}), status

    try:
        account_service.send_verification(user, request.host_url)
    except Exception:
        log.exception(f"Failed to send verification email to {user.get('email')}")

    session.permanent = True
    session["user_id"] = str(user.get("_id"))
    session["user"] = user.get("email")

    return jsonify({
        "success": True,
        "message": "Account created successfully. Check your email to verify your account.",
        "user": public_user(user),
    })


# -----------------------------------
# Logout
# -----------------------------------
@auth_routes.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})


# -----------------------------------
# Check Login Status
# -----------------------------------
@auth_routes.route("/api/user")
def current_user():
    if "user" not in session:
        return jsonify({"loggedIn": False})
    return jsonify({"loggedIn": True, "email": session["user"]})
