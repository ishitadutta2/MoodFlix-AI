"""
utils/colors.py
---------------------------------------
Deterministic color helper
MoodFlix AI

Gives any piece of text (a movie/song title, a chat title, ...) a
stable hue value, so the same item always renders with the same
gradient tile color across pages.
"""

import hashlib


def hue_for(text: str) -> int:
    if not text:
        return 220
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest, 16) % 360
