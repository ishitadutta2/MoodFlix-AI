"""
database/favorite_model.py
---------------------------------------
Favorite Model
MoodFlix AI
"""

from datetime import datetime


# =====================================================
# Create Favorite
# =====================================================

def create_favorite(
    user_id: str,
    content_type: str,
    title: str,
    image: str = "",
    description: str = "",
    language: str = "",
    genre: str = "",
    year: str = "",
    rating: float = 0.0,
    list_name: str = "favorites",
    artist: str = "",
    folder: str = "",
):
    """
    Create a favorite (or watch-later) document.

    content_type:
        movie
        song
        anime
        tv_show
        book

    list_name:
        favorites
        watch_later
    """

    return {

        "user_id": user_id,

        "content_type": content_type,

        "title": title,

        "artist": artist,

        "image": image,

        "description": description,

        "language": language,

        "genre": genre,

        "year": year,

        "rating": rating,

        "list": list_name,

        "folder": folder,

        "created_at": datetime.utcnow()
    }


# =====================================================
# Public Favorite
# =====================================================

def public_favorite(favorite):

    if not favorite:
        return None

    return {

        "id": str(favorite.get("_id")),

        "content_type": favorite.get("content_type"),

        "title": favorite.get("title"),

        "artist": favorite.get("artist"),

        "image": favorite.get("image"),

        "description": favorite.get("description"),

        "language": favorite.get("language"),

        "genre": favorite.get("genre"),

        "year": favorite.get("year"),

        "rating": favorite.get("rating"),

        "list": favorite.get("list", "favorites"),

        "folder": favorite.get("folder", ""),

        "created_at": favorite.get("created_at")
    }
