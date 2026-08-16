"""
app.py
----------------------------------------------------
MoodFlix AI
Main Flask Application

Run (development):
    python app.py

Run (production):
    gunicorn -w 4 -b 0.0.0.0:5000 app:app

Then open:
    http://127.0.0.1:5000
----------------------------------------------------
"""

import os

from flask import Flask, jsonify, render_template, request, session
from dotenv import load_dotenv
from pymongo.errors import PyMongoError

import config
from extensions import limiter, cache, compress
from utils.logger import configure_logging, get_logger
from utils.csrf import ensure_csrf_token, csrf_protect

from routes import (
    page_routes,
    auth_routes,
    chat_routes,
    history_routes,
    favorite_routes,
    profile_routes,
    feedback_routes,
    search_routes,
    analytics_routes,
    password_reset_routes,
    verification_routes,
    calendar_routes,
)

# Load environment variables
load_dotenv()

log = get_logger("app")


def create_app():
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # -----------------------------------
    # Logging
    # -----------------------------------
    configure_logging(app)

    # -----------------------------------
    # Load Configuration
    # -----------------------------------
    environment = os.getenv("FLASK_ENV", "development")
    app.config.from_object(
        config.config.get(environment, config.config["development"])
    )

    if environment == "production" and app.config["SECRET_KEY"] == "change-this-secret-key":
        log.warning(
            "Running in production with the default SECRET_KEY. "
            "Set SECRET_KEY in your .env before deploying for real."
        )

    # -----------------------------------
    # Extensions
    # -----------------------------------
    limiter.init_app(app)
    cache.init_app(app)
    compress.init_app(app)

    # -----------------------------------
    # Register Blueprints
    # -----------------------------------
    app.register_blueprint(page_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(chat_routes)
    app.register_blueprint(history_routes)
    app.register_blueprint(favorite_routes)
    app.register_blueprint(profile_routes)
    app.register_blueprint(feedback_routes)
    app.register_blueprint(search_routes)
    app.register_blueprint(analytics_routes)
    app.register_blueprint(password_reset_routes)
    app.register_blueprint(verification_routes)
    app.register_blueprint(calendar_routes)

    # -----------------------------------
    # CSRF protection (double-submit token — see utils/csrf.py)
    # -----------------------------------
    @app.before_request
    def _csrf_before_request():
        ensure_csrf_token()
        return csrf_protect()

    @app.route("/api/csrf-token")
    def get_csrf_token():
        return jsonify({"csrf_token": ensure_csrf_token()})

    @app.route("/api/version")
    def get_version():
        return jsonify({"version": config.APP_VERSION})

    # -----------------------------------
    # Security headers (Helmet-equivalent)
    # -----------------------------------
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
        # CSP allows the specific CDNs already used (lucide, marked, DOMPurify).
        # 'unsafe-inline' is required because templates use inline <script>/style
        # blocks throughout (CSRF token bootstrapping, gradient tiles, etc.) —
        # tightening this further means moving all of those to external files.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'"
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # -----------------------------------
    # Shared template context
    # -----------------------------------
    @app.context_processor
    def inject_globals():
        from services import chat_service, cache_service

        user_id = session.get("user_id")
        chat_groups = []
        if user_id:
            recent = cache_service.get_sidebar_chats(user_id)
            if recent is None:
                recent = chat_service.list_chats(user_id)[:15]
                cache_service.set_sidebar_chats(user_id, recent)
            if recent:
                chat_groups = [{"label": "Recent", "chats": recent}]

        return {
            "chat_groups": chat_groups,
            "csrf_token": ensure_csrf_token(),
            "app_version": config.APP_VERSION,
        }

    # -----------------------------------
    # Error Handlers
    # -----------------------------------
    # API routes (/api/...) get JSON errors; page routes get the HTML 404.
    # (page_routes also registers its own 404 template handler via
    # @page_routes.app_errorhandler, which Flask will use for non-API 404s.)

    def _wants_json():
        return request.path.startswith("/api/")

    @app.errorhandler(400)
    def bad_request(error):
        if _wants_json():
            return jsonify({"success": False, "message": "Bad request."}), 400
        return render_template("404.html"), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if _wants_json():
            return jsonify({"success": False, "message": "Authentication required."}), 401
        return render_template("404.html"), 401

    @app.errorhandler(403)
    def forbidden(error):
        message = "You don't have permission to do that."
        if _wants_json():
            return jsonify({"success": False, "message": message}), 403
        return render_template("404.html"), 403

    @app.errorhandler(413)
    def payload_too_large(error):
        message = "Upload too large. Max file size is 5 MB."
        if _wants_json():
            return jsonify({"success": False, "message": message}), 413
        return render_template("404.html"), 413

    @app.errorhandler(423)
    def account_locked(error):
        # Raised manually with a specific message by auth_routes; this
        # handler only covers the generic case.
        message = "This account is temporarily locked. Please try again later."
        if _wants_json():
            return jsonify({"success": False, "message": message}), 423
        return render_template("404.html"), 423

    @app.errorhandler(429)
    def rate_limited(error):
        message = "Too many requests. Please slow down and try again shortly."
        if _wants_json():
            return jsonify({"success": False, "message": message}), 429
        return render_template("404.html"), 429

    @app.errorhandler(PyMongoError)
    def database_error(error):
        log.exception("Database error")
        message = "Database temporarily unavailable. Please try again in a moment."
        if _wants_json():
            return jsonify({"success": False, "message": message}), 503
        return render_template("404.html"), 503

    @app.errorhandler(500)
    def server_error(error):
        log.exception("Unhandled server error")
        message = "Something went wrong on our end. Please try again."
        if _wants_json():
            return jsonify({"success": False, "message": message}), 500
        return render_template("404.html"), 500

    return app


# Create App
app = create_app()


# -----------------------------------
# Run Server
# -----------------------------------
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", 5000)),
        debug=app.config["DEBUG"],
    )
