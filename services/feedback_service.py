"""
services/feedback_service.py
---------------------------------------
Feedback Service
MoodFlix AI
"""

from database.repositories import feedback_repo
from database.feedback_model import create_feedback, public_feedback
from utils.logger import get_logger

log = get_logger("feedback_service")

ALLOWED_REACTIONS = ["loved", "disliked"]


def add_feedback(user_id: str, data: dict):
    """Returns (feedback_dict, error_message)."""

    title = str(data.get("title", "")).strip()
    reaction = str(data.get("reaction", "")).strip().lower()
    content_type = str(data.get("content_type", "")).strip().lower()
    genre = str(data.get("genre", "")).strip()
    chat_id = data.get("chat_id")

    if not title:
        return None, "Title is required."

    if reaction not in ALLOWED_REACTIONS:
        return None, f"Reaction must be one of: {', '.join(ALLOWED_REACTIONS)}."

    doc = create_feedback(user_id, title, content_type, genre, reaction, chat_id)
    doc = feedback_repo.insert_one(doc)

    log.info(f"user={user_id} reaction={reaction} title={title!r}")

    return public_feedback(doc), None


def get_signals(user_id: str):
    """
    Returns {"loved_genres": [...], "disliked_genres": [...], "loved_titles": [...], "disliked_titles": [...]}
    used to bias future recommendations.
    """

    docs = feedback_repo.find_by_user(user_id)

    loved_genres, disliked_genres = set(), set()
    loved_titles, disliked_titles = set(), set()

    for d in docs:
        genre = d.get("genre")
        title = d.get("title")
        if d.get("reaction") == "loved":
            if genre:
                loved_genres.add(genre)
            if title:
                loved_titles.add(title)
        elif d.get("reaction") == "disliked":
            if genre:
                disliked_genres.add(genre)
            if title:
                disliked_titles.add(title)

    return {
        "loved_genres": list(loved_genres),
        "disliked_genres": list(disliked_genres),
        "loved_titles": list(loved_titles),
        "disliked_titles": list(disliked_titles),
    }


def acceptance_rate(user_id: str, total_recommendations: int):
    """
    Rough "recommendation accuracy" proxy: loved reactions divided by
    total recommendation slots shown. There's no ground truth for
    "accuracy" without real user studies, so treat this as an
    approximation, not a precise metric.
    """

    if total_recommendations <= 0:
        return 0

    loved_count = len(feedback_repo.find_by_user(user_id, reaction="loved"))

    return round(min(loved_count / total_recommendations, 1.0) * 100, 1)
