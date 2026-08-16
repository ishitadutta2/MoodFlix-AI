"""
routes/verification_routes.py
---------------------------------------
Email Verification Routes
MoodFlix AI
"""

from flask import Blueprint, request, jsonify, render_template, g

from services import account_service
from extensions import limiter
from utils.auth import login_required

verification_routes = Blueprint("verification_routes", __name__)


@verification_routes.route("/verify-email")
def verify_email_page():
    token = request.args.get("token", "")
    ok, error = account_service.verify_email(token) if token else (False, "Missing verification token.")
    return render_template("verify_email.html", ok=ok, error=error)


@verification_routes.route("/api/resend-verification", methods=["POST"])
@login_required
@limiter.limit("3 per minute")
def resend_verification():
    if g.current_user.get("is_verified"):
        return jsonify({"success": False, "message": "Your email is already verified."}), 400

    account_service.send_verification(g.current_user, request.host_url)
    return jsonify({"success": True, "message": "Verification email sent."})
