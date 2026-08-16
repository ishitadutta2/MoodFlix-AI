"""
utils/csrf.py
---------------------------------------
CSRF protection
MoodFlix AI

The frontend is JSON/fetch-based rather than classic HTML forms, so
Flask-WTF's form-field CSRF doesn't apply cleanly. Instead we use the
double-submit-token pattern:

1. Every session gets a random csrf_token (set in `before_request`).
2. The token is exposed to JS via a global on every rendered page.
3. `apiFetch()` (static/js/base.js) attaches it as an X-CSRF-Token header
   on every state-changing request.
4. `before_request` rejects POST/PUT/DELETE/PATCH requests to /api/*
   whose header doesn't match the session's token.

Because the token lives in the (signed, HttpOnly) session cookie and is
only ever read back out by our own JS, an attacker's cross-site page
can't forge a matching header value.
"""

import secrets

from flask import session, request, jsonify

EXEMPT_ENDPOINTS = {
    # Auth endpoints a visitor may hit before a session exists.
    "auth_routes.login",
    "auth_routes.signup",
}


def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)
    return session["csrf_token"]


def csrf_protect():
    """Call from app.before_request."""

    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return None

    if not request.path.startswith("/api/"):
        return None

    if request.endpoint in EXEMPT_ENDPOINTS:
        return None

    token = session.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    if not token or not header_token or not secrets.compare_digest(token, header_token):
        return jsonify({
            "success": False,
            "message": "Your session expired. Please refresh the page and try again."
        }), 403

    return None
