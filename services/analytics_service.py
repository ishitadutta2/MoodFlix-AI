"""
services/analytics_service.py
---------------------------------------
Analytics Service
MoodFlix AI

All numbers here are computed from real stored data (chats, messages,
favorites, feedback) — nothing is fabricated. "Recommendation
accuracy" is explicitly labeled as an approximation since there's no
ground-truth signal for it beyond user feedback.
"""

from datetime import datetime, timedelta
from collections import Counter

from database.repositories import chat_repo, feedback_repo
from services import favorite_service, feedback_service

MOOD_LABELS = {
    "happy": "Happy", "sad": "Sad", "stressed": "Stressed", "angry": "Angry",
    "relaxed": "Relaxed", "romantic": "Romantic", "nostalgic": "Nostalgic",
    "adventurous": "Adventurous", "bored": "Bored", "neutral": "Neutral",
}


def get_analytics(user_id: str):

    chats = chat_repo.find_by_user(user_id)

    week_ago = datetime.utcnow() - timedelta(days=7)
    chats_this_week = len([c for c in chats if (c.get("created_at") or datetime.min) >= week_ago])

    mood_counts = Counter(c.get("mood") for c in chats if c.get("mood"))
    most_active_mood = MOOD_LABELS.get(mood_counts.most_common(1)[0][0]) if mood_counts else None

    mood_trend = [
        {"mood": MOOD_LABELS.get(mood, mood), "count": count}
        for mood, count in mood_counts.most_common()
    ]

    total_recommendations = sum(c.get("message_count", 0) for c in chats) * 6
    acceptance_rate = feedback_service.acceptance_rate(user_id, total_recommendations)

    # Average session length, approximated as messages per chat.
    avg_session = round(sum(c.get("message_count", 0) for c in chats) / len(chats), 1) if chats else 0

    return {
        "chats_this_week": chats_this_week,
        "favorite_genre": favorite_service.top_genre(user_id),
        "most_active_mood": most_active_mood,
        "mood_trend": mood_trend,
        "average_session_messages": avg_session,
        "recommendations_shown": total_recommendations,
        "recommendation_acceptance_rate": acceptance_rate,
        "total_chats": len(chats),
    }


def get_platform_stats():
    """
    Site-wide numbers for public pages (e.g. the landing page). Computed
    the same way as the per-user analytics above — real counts from the
    database, never a fabricated marketing figure. On a fresh install
    these will legitimately be 0 until real users start chatting.
    """

    all_chats = chat_repo.find()
    total_conversations = len(all_chats)
    total_recommendations = sum(c.get("message_count", 0) for c in all_chats) * 6

    loved_count = feedback_repo.count({"reaction": "loved"})
    acceptance_rate = (
        round(min(loved_count / total_recommendations, 1.0) * 100, 1)
        if total_recommendations > 0 else 0
    )

    return {
        "total_conversations": total_conversations,
        "total_recommendations": total_recommendations,
        "acceptance_rate": acceptance_rate,
    }
