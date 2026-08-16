"""
services/dashboard_service.py
---------------------------------------
Dashboard Service
MoodFlix AI

get_dashboard_data(user) is the single entry point page_routes.py
calls — routes should not be running Mongo queries themselves.
Results are cached briefly per-user (see services/cache_service.py)
since the dashboard is the most frequently-loaded page in the app.
"""

from datetime import datetime
from collections import Counter

from database.repositories import favorite_repo, chat_repo
from database.user_model import public_user
from utils.colors import hue_for
from services import cache_service
from services.favorite_service import counts as favorite_counts

# Rough "positivity" score per mood, used only to drive the circular
# mood meter's fill — not a clinical measure of anything.
MOOD_SCORE = {
    "happy": 90, "relaxed": 80, "romantic": 75, "adventurous": 70,
    "nostalgic": 60, "neutral": 50, "bored": 40, "stressed": 30,
    "sad": 20, "angry": 15,
}
MOOD_EMOJI = {
    "happy": "😄", "sad": "😢", "stressed": "😖", "angry": "😠",
    "relaxed": "😌", "romantic": "💕", "nostalgic": "🥹",
    "adventurous": "🤠", "bored": "😐", "neutral": "🙂",
}


def get_dashboard_data(user: dict) -> dict:

    user_id = str(user.get("_id"))

    cached = cache_service.get_dashboard(user_id)
    if cached is not None:
        return cached

    favorite_movies = [
        _with_hue(f)
        for f in favorite_repo.find_by_user(user_id, list_name="favorites", content_type="movie")[:5]
    ]
    favorite_songs = [
        _with_hue(f)
        for f in favorite_repo.find_by_user(user_id, list_name="favorites", content_type="song")[:5]
    ]

    fav_counts = favorite_counts(user_id)
    all_chats = chat_repo.find_by_user(user_id)
    total_chats = len(all_chats)

    today = datetime.utcnow().date()
    today_chats = [c for c in all_chats if c.get("created_at") and c["created_at"].date() == today]
    today_mood = None
    if today_chats:
        mood_counts = Counter(c.get("mood") for c in today_chats if c.get("mood"))
        today_mood = mood_counts.most_common(1)[0][0] if mood_counts else "neutral"

    all_favorites = favorite_repo.find_by_user(user_id, list_name="favorites")
    today_favorite_count = len([
        f for f in all_favorites if f.get("created_at") and f["created_at"].date() == today
    ])

    data = {
        "user": public_user(user),
        "active_page": "dashboard",
        "movies": [],
        "songs": [],
        "genres": user.get("favorite_genres", []),
        "favorite_movies": favorite_movies,
        "favorite_songs": favorite_songs,
        "artist_avatars": [],
        "artist_overflow": 0,
        "total_chats": total_chats,
        "total_favorites": fav_counts["total"],
        "today_mood": today_mood,
        "today_mood_emoji": MOOD_EMOJI.get(today_mood, ""),
        "today_mood_score": MOOD_SCORE.get(today_mood, 0),
        "today_chat_count": len(today_chats),
        "today_favorite_count": today_favorite_count,
    }

    cache_service.set_dashboard(user_id, data)

    return data


def _with_hue(favorite_doc):
    return {
        "id": str(favorite_doc.get("_id")),
        "title": favorite_doc.get("title"),
        "artist": favorite_doc.get("artist", ""),
        "hue": hue_for(favorite_doc.get("title", "")),
    }
