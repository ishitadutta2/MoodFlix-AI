"""
database/user_model.py
---------------------------------------
User Model
MoodFlix AI
"""

from datetime import datetime


def create_user(
    name: str,
    email: str,
    password: str
):
    """
    Create a new user document.
    Password should already be hashed.
    """

    return {
        "name": name,
        "email": email.lower(),
        "password": password,

        "profile_picture": "",

        "bio": "",

        "favorite_genres": [],

        "favorite_languages": [],

        "favorite_artists": [],

        "favorite_actors": [],

        "favorite_movies": [],

        "favorite_songs": [],

        "favorite_platforms": [],

        "theme_preference": "dark",

        "accent_color": "#8B5CF6",

        "notification_settings": {
            "weekly_digest": True,
            "recommendation_alerts": True,
            "marketing_emails": False,
        },

        "privacy_settings": {
            "show_favorites_publicly": False,
            "show_activity_publicly": False,
        },

        "is_verified": False,

        # Account lockout (brute-force protection)
        "failed_login_attempts": 0,

        "locked_until": None,

        "created_at": datetime.utcnow(),

        "updated_at": datetime.utcnow()
    }


def public_user(user: dict):
    """
    Remove sensitive information before
    sending data to the frontend.
    """

    if not user:
        return None

    return {
        "id": str(user.get("_id")) if user.get("_id") else None,
        "name": user.get("name"),
        "email": user.get("email"),
        "profile_picture": user.get("profile_picture"),
        "bio": user.get("bio"),
        "favorite_genres": user.get("favorite_genres", []),
        "favorite_languages": user.get("favorite_languages", []),
        "favorite_artists": user.get("favorite_artists", []),
        "favorite_actors": user.get("favorite_actors", []),
        "favorite_movies": user.get("favorite_movies", []),
        "favorite_songs": user.get("favorite_songs", []),
        "favorite_platforms": user.get("favorite_platforms", []),
        "theme_preference": user.get("theme_preference", "dark"),
        "accent_color": user.get("accent_color", "#8B5CF6"),
        "notification_settings": user.get("notification_settings", {
            "weekly_digest": True, "recommendation_alerts": True, "marketing_emails": False,
        }),
        "privacy_settings": user.get("privacy_settings", {
            "show_favorites_publicly": False, "show_activity_publicly": False,
        }),
        "is_verified": user.get("is_verified", False),
        "created_at": user.get("created_at")
    }


def update_profile(
    user: dict,
    data: dict
):
    """
    Update editable profile fields.
    """

    allowed_fields = [
        "name",
        "bio",
        "profile_picture",
        "favorite_genres",
        "favorite_languages",
        "favorite_artists",
        "favorite_actors",
        "favorite_movies",
        "favorite_songs",
        "favorite_platforms",
        "theme_preference",
        "accent_color",
        "notification_settings",
        "privacy_settings",
    ]

    for field in allowed_fields:

        if field in data:
            user[field] = data[field]

    user["updated_at"] = datetime.utcnow()

    return user
