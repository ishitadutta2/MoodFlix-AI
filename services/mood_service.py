"""
services/mood_service.py
---------------------------------------
Mood Detection
MoodFlix AI

There's no sentiment-analysis API wired into this project, so this
uses a small keyword lexicon instead of a real NLP model. It's a
reasonable heuristic for tagging chat mood/history/analytics, but it
will misclassify sarcasm, negation, and anything outside the lexicon.
Swap this for a real model (e.g. a Gemini classification prompt, or
a proper sentiment library) if you need higher accuracy.
"""

import re

MOOD_LEXICON = {
    "happy": ["happy", "excited", "great", "awesome", "good mood", "cheerful", "joyful", "pumped", "thrilled"],
    "sad": ["sad", "down", "depressed", "crying", "heartbroken", "lonely", "blue", "grief", "miss"],
    "stressed": ["stressed", "anxious", "overwhelmed", "worried", "nervous", "pressure", "burnt out", "exhausted"],
    "angry": ["angry", "mad", "furious", "frustrated", "annoyed", "pissed"],
    "relaxed": ["relaxed", "calm", "chill", "cozy", "peaceful", "lazy sunday", "unwind"],
    "romantic": ["romantic", "date night", "love", "crush", "valentine"],
    "nostalgic": ["nostalgic", "throwback", "childhood", "remember when", "old school"],
    "adventurous": ["adventurous", "road trip", "explore", "adrenaline", "thrill"],
    "bored": ["bored", "nothing to do", "meh", "dull"],
}


def detect_mood(text: str) -> str:
    """Returns a mood label, or 'neutral' if nothing matches."""

    if not text:
        return "neutral"

    lowered = text.lower()

    scores = {}
    for mood, keywords in MOOD_LEXICON.items():
        count = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", lowered))
        if count:
            scores[mood] = count

    if not scores:
        return "neutral"

    return max(scores, key=scores.get)
