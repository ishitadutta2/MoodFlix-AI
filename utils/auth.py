"""
utils/auth.py
---------------------------------------
Shared authentication helpers
MoodFlix AI
"""

from functools import wraps
from datetime import datetime, timedelta

from flask import session, jsonify, redirect, url_for, g

from database.repositories import user_repo
from database.ids import parse_id

# Idle timeout — independent of the absolute PERMANENT_SESSION_LIFETIME.
# If the person hasn't made a request in this long, treat them as logged out
# even if the signed cookie itself hasn't expired yet.
IDLE_TIMEOUT_MINUTES = 60


def _load_current_user():
    """Fetch the logged-in user's document (or None) and cache it on `g`."""

    if "user_id" not in session:
        return None

    if hasattr(g, "_current_user_loaded"):
        return g._current_user

    last_seen = session.get("last_activity")
    if last_seen:
        idle_for = datetime.utcnow() - datetime.fromisoformat(last_seen)
        if idle_for > timedelta(minutes=IDLE_TIMEOUT_MINUTES) and not session.get("remember_me"):
            session.clear()
            g._current_user = None
            g._current_user_loaded = True
            return None

    session["last_activity"] = datetime.utcnow().isoformat()

    user = user_repo.find_by_id(parse_id(session["user_id"]))
    g._current_user = user
    g._current_user_loaded = True

    if not user:
        # Stale session pointing at a user that no longer exists.
        session.clear()

    return user


def get_current_user():
    """Public accessor other routes can use to fetch the logged-in user."""
    return _load_current_user()


def login_required(view):
    """
    Protects JSON API routes.
    Returns a 401 JSON response instead of redirecting.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _load_current_user()

        if not user:
            return jsonify({
                "success": False,
                "message": "You must be logged in to do that."
            }), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def login_required_page(view):
    """
    Protects HTML page routes.
    Redirects to the login page instead of returning JSON.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _load_current_user()

        if not user:
            return redirect(url_for("page_routes.login"))

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped
