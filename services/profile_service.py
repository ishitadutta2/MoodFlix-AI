"""
services/profile_service.py
---------------------------------------
Profile Service
MoodFlix AI
"""

import os
import uuid

from PIL import Image, UnidentifiedImageError

from database.repositories import user_repo, chat_repo, message_repo, favorite_repo
from database.user_model import public_user, update_profile as apply_profile_update
from services.auth_service import hash_password, verify_password, validate_password
from services import cache_service
from utils.logger import get_logger

log = get_logger("profile_service")

MAX_NAME_LENGTH = 100
MAX_BIO_LENGTH = 500
MAX_LIST_ITEM_LENGTH = 100
MAX_LIST_LENGTH = 25
MAX_AVATAR_DIMENSION = 512
ALLOWED_THEMES = {"dark", "light", "system"}

LIST_FIELDS = (
    "favorite_genres", "favorite_languages", "favorite_artists",
    "favorite_actors", "favorite_movies", "favorite_songs", "favorite_platforms",
)

NOTIFICATION_KEYS = {"weekly_digest", "recommendation_alerts", "marketing_emails"}
PRIVACY_KEYS = {"show_favorites_publicly", "show_activity_publicly"}


def _clean_list_field(value):
    if not isinstance(value, list):
        return None
    cleaned = [str(v).strip()[:MAX_LIST_ITEM_LENGTH] for v in value if str(v).strip()]
    return cleaned[:MAX_LIST_LENGTH]


def _clean_bool_map(value, allowed_keys, current: dict):
    """Merge a partial {key: bool} dict into the existing settings dict."""
    if not isinstance(value, dict):
        return None
    merged = dict(current or {})
    for k, v in value.items():
        if k not in allowed_keys:
            return None
        merged[k] = bool(v)
    return merged


def update_profile(user: dict, data: dict):
    """Returns (updated_public_user, error_message)."""

    updates = {}

    if "name" in data:
        name = str(data.get("name", "")).strip()
        if not name:
            return None, "Name is required."
        if len(name) > MAX_NAME_LENGTH:
            return None, f"Name must be under {MAX_NAME_LENGTH} characters."
        updates["name"] = name

    if "bio" in data:
        bio = str(data.get("bio", "")).strip()
        if len(bio) > MAX_BIO_LENGTH:
            return None, f"Bio must be under {MAX_BIO_LENGTH} characters."
        updates["bio"] = bio

    if "theme_preference" in data:
        theme = str(data.get("theme_preference", "")).strip().lower()
        if theme not in ALLOWED_THEMES:
            return None, f"Theme must be one of: {', '.join(ALLOWED_THEMES)}."
        updates["theme_preference"] = theme

    if "accent_color" in data:
        color = str(data.get("accent_color", "")).strip()
        if not color.startswith("#") or len(color) not in (4, 7):
            return None, "Accent color must be a hex value like #8B5CF6."
        updates["accent_color"] = color

    if "notification_settings" in data:
        merged = _clean_bool_map(data.get("notification_settings"), NOTIFICATION_KEYS, user.get("notification_settings"))
        if merged is None:
            return None, f"notification_settings keys must be one of: {', '.join(sorted(NOTIFICATION_KEYS))}."
        updates["notification_settings"] = merged

    if "privacy_settings" in data:
        merged = _clean_bool_map(data.get("privacy_settings"), PRIVACY_KEYS, user.get("privacy_settings"))
        if merged is None:
            return None, f"privacy_settings keys must be one of: {', '.join(sorted(PRIVACY_KEYS))}."
        updates["privacy_settings"] = merged

    for field in LIST_FIELDS:
        if field in data:
            cleaned = _clean_list_field(data.get(field))
            if cleaned is None:
                return None, f"{field} must be a list of text values."
            updates[field] = cleaned

    if not updates:
        return None, "No valid fields to update."

    updated_user = apply_profile_update(dict(user), updates)
    user_repo.update_one(
        {"_id": user["_id"]},
        {"$set": {k: updated_user[k] for k in list(updates.keys()) + ["updated_at"]}},
    )

    cache_service.invalidate_dashboard(str(user["_id"]))
    log.info(f"user={user['_id']} updated profile fields: {list(updates.keys())}")

    return public_user(updated_user), None


def update_avatar(user: dict, file_storage, upload_root: str):
    """
    Validates the uploaded file is actually a decodable image (not just
    a file with an image-like extension), resizes it, and saves it.
    Returns (avatar_url, error_message).
    """

    if not file_storage or file_storage.filename == "":
        return None, "No file selected."

    try:
        image = Image.open(file_storage.stream)
        image.verify()  # raises if not a real image
        # verify() consumes the file object; reopen to actually use it.
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream)
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError):
        return None, "That file doesn't look like a valid image."

    image.thumbnail((MAX_AVATAR_DIMENSION, MAX_AVATAR_DIMENSION))

    user_id = str(user["_id"])
    filename = f"{user_id}-{uuid.uuid4().hex[:8]}.jpg"
    avatar_dir = os.path.join(upload_root, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    dest_path = os.path.join(avatar_dir, filename)
    image.save(dest_path, format="JPEG", quality=85)

    avatar_url = f"/static/uploads/avatars/{filename}"

    user_repo.update_one({"_id": user["_id"]}, {"$set": {"profile_picture": avatar_url}})
    cache_service.invalidate_dashboard(user_id)
    log.info(f"user={user_id} updated avatar")

    return avatar_url, None


def change_password(user: dict, current_password: str, new_password: str):
    """Returns (ok: bool, error_message)."""

    if not current_password or not new_password:
        return False, "Current and new passwords are required."

    if not verify_password(current_password, user.get("password", "")):
        return False, "Current password is incorrect."

    ok, message = validate_password(new_password)
    if not ok:
        return False, message

    user_repo.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": hash_password(new_password)}},
    )
    log.info(f"user={user['_id']} changed password")

    return True, None


def delete_account(user: dict):
    user_id = str(user["_id"])

    for chat_doc in chat_repo.find_by_user(user_id):
        message_repo.delete_by_chat(str(chat_doc["_id"]))
        chat_repo.delete_one({"_id": chat_doc["_id"]})

    favorite_repo.delete_all_for_user(user_id)

    user_repo.delete_one({"_id": user["_id"]})
    cache_service.invalidate_dashboard(user_id)
    log.info(f"user={user_id} deleted their account")


def get_stats(user: dict):
    from services import feedback_service

    user_id = str(user["_id"])

    user_chats = chat_repo.find_by_user(user_id)
    total_chats = len(user_chats)
    favorite_movies = len(favorite_repo.find_by_user(user_id, content_type="movie"))
    favorite_songs = len(favorite_repo.find_by_user(user_id, content_type="song"))

    # Each completed chat exchange produces 6 recommendation slots (3 movies + 3 songs).
    total_recommendations = sum(c.get("message_count", 0) for c in user_chats) * 6
    acceptance_rate = feedback_service.acceptance_rate(user_id, total_recommendations)

    return {
        "total_chats": total_chats,
        "favorite_movies": favorite_movies,
        "favorite_songs": favorite_songs,
        "recommendations_received": sum(c.get("message_count", 0) for c in user_chats),
        "recommendation_acceptance_rate": acceptance_rate,
    }
