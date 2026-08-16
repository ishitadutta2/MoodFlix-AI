"""
services/search_service.py
---------------------------------------
Search Service
MoodFlix AI

There's no external movie/music catalog wired in (no TMDB/Spotify API
key configured), so "search everywhere" is scoped to what's actually
in the database: the user's own chats, messages, favorites, and
saved taste preferences (genres/artists/actors/languages).
"""

from database.repositories import chat_repo, message_repo, favorite_repo


def search(user_id: str, query: str, user: dict = None):
    query_lower = (query or "").strip().lower()

    if not query_lower:
        return {"chats": [], "favorites": [], "messages": [], "genres": [], "artists": [], "actors": []}

    chats = chat_repo.find_by_user(user_id)
    chat_matches = [_chat_summary(c) for c in chats if query_lower in (c.get("title") or "").lower()]

    favorites = favorite_repo.find_by_user(user_id)
    favorite_matches = [
        _favorite_summary(f) for f in favorites
        if query_lower in (f.get("title") or "").lower()
        or query_lower in (f.get("artist") or "").lower()
        or query_lower in (f.get("genre") or "").lower()
    ]

    # Search inside message text too (limited to this user's own chats).
    chat_ids = {str(c["_id"]) for c in chats}
    matching_messages = [
        {"chat_id": m.get("chat_id"), "sender": m.get("sender"), "snippet": (m.get("message") or "")[:160]}
        for m in message_repo.search_text(chat_ids, query_lower, limit=20)
    ]

    # Match against saved taste preferences (genres/artists/actors/languages) —
    # both what's in favorites AND what's saved on the user's profile.
    genre_pool = set(f.get("genre") for f in favorites if f.get("genre"))
    artist_pool = set(f.get("artist") for f in favorites if f.get("artist"))
    if user:
        genre_pool |= set(user.get("favorite_genres", []))
        artist_pool |= set(user.get("favorite_artists", []))
        actor_pool = set(user.get("favorite_actors", []))
    else:
        actor_pool = set()

    genre_matches = sorted([g for g in genre_pool if query_lower in g.lower()])
    artist_matches = sorted([a for a in artist_pool if query_lower in a.lower()])
    actor_matches = sorted([a for a in actor_pool if query_lower in a.lower()])

    return {
        "chats": chat_matches[:20],
        "favorites": favorite_matches[:20],
        "messages": matching_messages,
        "genres": genre_matches[:10],
        "artists": artist_matches[:10],
        "actors": actor_matches[:10],
    }


def _chat_summary(chat):
    return {
        "id": str(chat.get("_id")),
        "title": chat.get("title"),
        "last_message": chat.get("last_message"),
    }


def _favorite_summary(favorite):
    return {
        "id": str(favorite.get("_id")),
        "title": favorite.get("title"),
        "content_type": favorite.get("content_type"),
        "genre": favorite.get("genre"),
        "artist": favorite.get("artist"),
    }
