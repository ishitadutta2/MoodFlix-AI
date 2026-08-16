"""
routes/__init__.py

Exports all Flask blueprints.
"""

from .page_routes import page_routes
from .auth_routes import auth_routes
from .chat_routes import chat_routes
from .history_routes import history_routes
from .favorite_routes import favorite_routes
from .profile_routes import profile_routes
from .feedback_routes import feedback_routes
from .search_routes import search_routes
from .analytics_routes import analytics_routes
from .password_reset_routes import password_reset_routes
from .verification_routes import verification_routes
from .calendar_routes import calendar_routes

__all__ = [
    "page_routes",
    "auth_routes",
    "chat_routes",
    "history_routes",
    "favorite_routes",
    "profile_routes",
    "feedback_routes",
    "search_routes",
    "analytics_routes",
    "password_reset_routes",
    "verification_routes",
    "calendar_routes",
]
