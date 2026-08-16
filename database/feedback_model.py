"""
database/feedback_model.py
---------------------------------------
Feedback Model
MoodFlix AI

Captures "Loved it" / "Not for me" reactions on recommendation cards.
Used by the recommendation engine to avoid re-suggesting disliked
genres/titles, and by analytics to report on recommendation quality.
"""

from datetime import datetime


def create_feedback(user_id: str, title: str, content_type: str, genre: str, reaction: str, chat_id: str = None):
    """
    reaction: "loved" | "disliked"
    """

    return {
        "user_id": user_id,
        "chat_id": chat_id,
        "title": title,
        "content_type": content_type,
        "genre": genre,
        "reaction": reaction,
        "created_at": datetime.utcnow(),
    }


def public_feedback(doc):
    if not doc:
        return None
    return {
        "id": str(doc.get("_id")),
        "title": doc.get("title"),
        "content_type": doc.get("content_type"),
        "genre": doc.get("genre"),
        "reaction": doc.get("reaction"),
        "created_at": doc.get("created_at"),
    }
