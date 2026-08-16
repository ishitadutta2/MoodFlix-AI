"""
services/favorite_service.py
---------------------------------------
Favorite / Watchlist Service
MoodFlix AI

Routes should call these functions rather than touching the favorites
repository/collection directly.
"""

from database.repositories import favorite_repo
from database.favorite_model import create_favorite, public_favorite
from database.ids import parse_id
from utils.logger import get_logger

log = get_logger("favorite_service")

ALLOWED_TYPES = ["movie", "song", "anime", "tv_show", "book"]
ALLOWED_LISTS = ["favorites", "watch_later"]
MAX_TITLE_LENGTH = 200
MAX_TEXT_LENGTH = 1000


SORT_OPTIONS = {"newest", "oldest", "title", "rating"}


def list_favorites(user_id: str, list_name: str = None, content_type: str = None,
                    folder: str = None, search: str = None, sort: str = "newest"):
    docs = favorite_repo.find_by_user(user_id, list_name=list_name, content_type=content_type)

    if folder:
        docs = [d for d in docs if (d.get("folder") or "") == folder]

    if search:
        search_lower = search.strip().lower()
        docs = [
            d for d in docs
            if search_lower in (d.get("title") or "").lower()
            or search_lower in (d.get("artist") or "").lower()
            or search_lower in (d.get("genre") or "").lower()
        ]

    if sort not in SORT_OPTIONS:
        sort = "newest"
    if sort == "newest":
        docs.sort(key=lambda d: d.get("created_at") or 0, reverse=True)
    elif sort == "oldest":
        docs.sort(key=lambda d: d.get("created_at") or 0)
    elif sort == "title":
        docs.sort(key=lambda d: (d.get("title") or "").lower())
    elif sort == "rating":
        docs.sort(key=lambda d: d.get("rating") or 0, reverse=True)

    return [public_favorite(d) for d in docs]


def list_folders(user_id: str):
    docs = favorite_repo.find_by_user(user_id)
    folders = sorted(set(d.get("folder") for d in docs if d.get("folder")))
    return folders


def move_to_folder(user_id: str, favorite_id: str, folder: str):
    favorite = favorite_repo.find_owned(parse_id(favorite_id), user_id)
    if not favorite:
        return False, "Favorite not found."

    folder = (folder or "").strip()[:60]
    favorite_repo.update_one({"_id": favorite["_id"]}, {"$set": {"folder": folder}})
    return True, None


def bulk_delete(user_id: str, favorite_ids: list):
    deleted = 0
    for fav_id in favorite_ids or []:
        favorite = favorite_repo.find_owned(parse_id(fav_id), user_id)
        if favorite:
            favorite_repo.delete_one({"_id": favorite["_id"]})
            deleted += 1
    return deleted


def add_favorite(user_id: str, data: dict):
    """Returns (favorite_dict, error_message)."""

    item_type = str(data.get("type", "")).strip().lower()
    title = str(data.get("title", "")).strip()
    list_name = str(data.get("list", "favorites")).strip().lower() or "favorites"

    if item_type not in ALLOWED_TYPES:
        return None, f"Type must be one of: {', '.join(ALLOWED_TYPES)}."

    if list_name not in ALLOWED_LISTS:
        return None, f"List must be one of: {', '.join(ALLOWED_LISTS)}."

    if not title:
        return None, "Title is required."

    if len(title) > MAX_TITLE_LENGTH:
        return None, f"Title must be under {MAX_TITLE_LENGTH} characters."

    favorite_doc = create_favorite(
        user_id=user_id,
        content_type=item_type,
        title=title,
        image=str(data.get("image", ""))[:500],
        description=str(data.get("description", ""))[:MAX_TEXT_LENGTH],
        language=str(data.get("language", ""))[:100],
        genre=str(data.get("genre", ""))[:100],
        year=str(data.get("year", ""))[:20],
        rating=_safe_float(data.get("rating", 0.0)),
        list_name=list_name,
        artist=str(data.get("artist", ""))[:150],
        folder=str(data.get("folder", ""))[:60],
    )

    favorite_doc = favorite_repo.insert_one(favorite_doc)

    log.info(f"user={user_id} added favorite '{title}' ({item_type}, {list_name})")

    return public_favorite(favorite_doc), None


def remove_favorite(user_id: str, favorite_id: str):
    """Returns (ok: bool, error_message)."""

    favorite = favorite_repo.find_owned(parse_id(favorite_id), user_id)
    if not favorite:
        return False, "Favorite not found."

    favorite_repo.delete_one({"_id": favorite["_id"]})
    return True, None


def clear_favorites(user_id: str, list_name: str = None):
    favorite_repo.delete_all_for_user(user_id, list_name=list_name)


def counts(user_id: str):
    all_favs = favorite_repo.find_by_user(user_id, list_name="favorites")
    return {
        "total": len(all_favs),
        "movies": len([f for f in all_favs if f.get("content_type") == "movie"]),
        "songs": len([f for f in all_favs if f.get("content_type") == "song"]),
    }


def top_genre(user_id: str):
    """Most common genre across a user's favorites, or None."""

    favs = favorite_repo.find_by_user(user_id)
    genre_counts = {}
    for f in favs:
        genre = f.get("genre")
        if genre:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1

    if not genre_counts:
        return None

    return max(genre_counts, key=genre_counts.get)


def trending(limit: int = 10):
    """
    Most-favorited titles across ALL users. There's no external
    "trending" data source wired in, so this is derived from our own
    users' favorites — an honest proxy, not real box-office/chart data.
    """

    all_favs = favorite_repo.find({})
    tally = {}
    for f in all_favs:
        key = (f.get("title"), f.get("content_type"))
        if not key[0]:
            continue
        tally[key] = tally.get(key, 0) + 1

    ranked = sorted(tally.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"title": k[0], "content_type": k[1], "favorite_count": v} for k, v in ranked]


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
