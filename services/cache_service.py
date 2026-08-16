"""
services/cache_service.py
---------------------------------------
Caching helper
MoodFlix AI

Wraps extensions.cache (Flask-Caching, in-process SimpleCache) with a
couple of named helpers so callers don't have to construct cache keys
by hand, and so invalidation happens in exactly one place whenever a
user's chats/favorites/profile change.
"""

from extensions import cache

DASHBOARD_TTL_SECONDS = 20
SIDEBAR_TTL_SECONDS = 10


def dashboard_key(user_id: str) -> str:
    return f"dashboard:{user_id}"


def get_dashboard(user_id: str):
    return cache.get(dashboard_key(user_id))


def set_dashboard(user_id: str, data: dict):
    cache.set(dashboard_key(user_id), data, timeout=DASHBOARD_TTL_SECONDS)


def invalidate_dashboard(user_id: str):
    cache.delete(dashboard_key(user_id))
    cache.delete(f"sidebar_chats:{user_id}")


def get_sidebar_chats(user_id: str):
    return cache.get(f"sidebar_chats:{user_id}")


def set_sidebar_chats(user_id: str, chats: list):
    cache.set(f"sidebar_chats:{user_id}", chats, timeout=SIDEBAR_TTL_SECONDS)
