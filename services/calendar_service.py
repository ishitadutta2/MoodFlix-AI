"""
services/calendar_service.py
---------------------------------------
Mood Calendar Service
MoodFlix AI

Aggregates existing chat data (mood + created_at, already tracked by
chat_service/mood_service) into a per-day view — no new tracking
infrastructure needed, just a different lens on data we already have.
"""

import calendar
from collections import Counter
from datetime import datetime

from database.repositories import chat_repo

MOOD_EMOJI = {
    "happy": "😄", "sad": "😢", "stressed": "😖", "angry": "😠",
    "relaxed": "😌", "romantic": "💕", "nostalgic": "🥹",
    "adventurous": "🤠", "bored": "😐", "neutral": "🙂",
}


def get_month_calendar(user_id: str, year: int, month: int):
    """
    Returns {
        "days": [{"date": "2026-07-01", "day": 1, "mood": "happy", "emoji": "😄", "chat_count": 2}, ...],
        "days_in_month": 31,
    }
    Days with no chats have mood=None.
    """

    chats = chat_repo.find_by_user(user_id)

    by_day = {}
    for chat in chats:
        created = chat.get("created_at")
        if not created or created.year != year or created.month != month:
            continue
        by_day.setdefault(created.day, []).append(chat)

    days_in_month = calendar.monthrange(year, month)[1]
    days = []

    for day in range(1, days_in_month + 1):
        day_chats = by_day.get(day, [])
        mood = None
        if day_chats:
            mood_counts = Counter(c.get("mood") for c in day_chats if c.get("mood"))
            mood = mood_counts.most_common(1)[0][0] if mood_counts else "neutral"

        days.append({
            "date": f"{year:04d}-{month:02d}-{day:02d}",
            "day": day,
            "mood": mood,
            "emoji": MOOD_EMOJI.get(mood, "") if mood else "",
            "chat_count": len(day_chats),
        })

    return {"days": days, "days_in_month": days_in_month}


def get_day_detail(user_id: str, date_str: str):
    """Returns the list of chats created on a given YYYY-MM-DD date."""

    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

    chats = chat_repo.find_by_user(user_id)
    day_chats = [
        c for c in chats
        if c.get("created_at") and c["created_at"].date() == target
    ]

    return [
        {
            "id": str(c["_id"]),
            "title": c.get("title"),
            "mood": c.get("mood"),
            "emoji": MOOD_EMOJI.get(c.get("mood"), ""),
            "last_message": c.get("last_message"),
        }
        for c in day_chats
    ]
