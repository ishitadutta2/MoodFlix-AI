"""
services/gemini_service.py
---------------------------------------
Gemini Service
MoodFlix AI

If GEMINI_API_KEY is configured, real recommendations are generated
by Gemini (structured as JSON). Otherwise a deterministic mock
recommender is used, so the app is fully usable without an API key.
"""

import os
import json
import hashlib

from utils.logger import get_logger

log = get_logger("gemini_service")

MOVIE_POOL = [
    {"title": "The Midnight Library", "year": 2023, "genre": "Fantasy Drama"},
    {"title": "Spirited Away", "year": 2001, "genre": "Animation"},
    {"title": "Whiplash", "year": 2014, "genre": "Drama"},
    {"title": "Paddington 2", "year": 2017, "genre": "Comedy"},
    {"title": "Arrival", "year": 2016, "genre": "Sci-Fi"},
    {"title": "Amelie", "year": 2001, "genre": "Romantic Comedy"},
    {"title": "Parasite", "year": 2019, "genre": "Thriller"},
    {"title": "Your Name", "year": 2016, "genre": "Animation"},
    {"title": "The Grand Budapest Hotel", "year": 2014, "genre": "Comedy"},
    {"title": "Inside Out", "year": 2015, "genre": "Animation"},
]

SONG_POOL = [
    {"title": "Weightless", "artist": "Marconi Union", "genre": "Ambient", "duration": "8:10"},
    {"title": "Here Comes the Sun", "artist": "The Beatles", "genre": "Classic Rock", "duration": "3:05"},
    {"title": "Good Days", "artist": "SZA", "genre": "R&B", "duration": "4:39"},
    {"title": "Sunflower", "artist": "Post Malone", "genre": "Pop", "duration": "2:38"},
    {"title": "Clair de Lune", "artist": "Debussy", "genre": "Classical", "duration": "5:00"},
    {"title": "Three Little Birds", "artist": "Bob Marley", "genre": "Reggae", "duration": "3:00"},
    {"title": "Feel Good Inc.", "artist": "Gorillaz", "genre": "Alternative", "duration": "3:41"},
    {"title": "Circles", "artist": "Post Malone", "genre": "Pop Rock", "duration": "3:35"},
]


def _seeded_index(seed_text: str, salt: str, pool_len: int) -> int:
    digest = hashlib.sha256(f"{seed_text}:{salt}".encode("utf-8")).hexdigest()
    return int(digest, 16) % pool_len


def _mock_recommendations(user_message: str, avoid_titles=None, avoid_genres=None):
    """Deterministic but varied mock recommendations (no API key needed)."""

    avoid_titles = set(avoid_titles or [])
    avoid_genres = set(g.lower() for g in (avoid_genres or []))

    seed = user_message.strip().lower() or "moodflix"

    movie_candidates = [m for m in MOVIE_POOL if m["title"] not in avoid_titles and m["genre"].lower() not in avoid_genres] or MOVIE_POOL
    song_candidates = [s for s in SONG_POOL if s["title"] not in avoid_titles and s["genre"].lower() not in avoid_genres] or SONG_POOL

    movies = []
    for i in range(3):
        idx = _seeded_index(seed, f"movie-{i}", len(movie_candidates))
        m = dict(movie_candidates[idx])
        m["hue"] = _seeded_index(seed, f"hue-movie-{i}", 360)
        m["rating"] = round(6.5 + (_seeded_index(seed, f"rating-{i}", 35) / 10), 1)
        m["desc"] = f"A {m['genre'].lower()} pick that fits the mood behind \"{user_message[:60]}\"."
        m["why"] = "Recommended based on your message — connect a Gemini API key for deeper personalization."
        movies.append(m)

    songs = []
    for i in range(3):
        idx = _seeded_index(seed, f"song-{i}", len(song_candidates))
        s = dict(song_candidates[idx])
        s["hue"] = _seeded_index(seed, f"hue-song-{i}", 360)
        s["desc"] = f"A {s['genre'].lower()} track to match the moment."
        songs.append(s)

    reply = (
        f"Here's what I'm thinking based on \"{user_message.strip()}\" — "
        "a mix of movies and songs to match your mood. (Demo mode: connect "
        "a Gemini API key in your .env for real AI-generated picks.)"
    )

    return reply, movies, songs


def _gemini_recommendations(user_message: str, prompt: str):
    """Call the real Gemini API and parse a structured JSON response."""

    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # gemini-1.5-flash was retired by Google (all 1.0/1.5 models are shut
    # down and return 404 as of 2026) — use the current fast model instead.
    model = genai.GenerativeModel("gemini-flash-latest")

    structured_prompt = f"""{prompt}

Respond ONLY with valid JSON (no markdown fences, no commentary) in this exact shape:
{{
  "reply": "a short friendly reply message",
  "movies": [
    {{"title": "", "year": 2020, "genre": "", "desc": "", "rating": 8.0, "why": "", "hue": 210}}
  ],
  "songs": [
    {{"title": "", "artist": "", "genre": "", "duration": "3:30", "desc": "", "hue": 210}}
  ]
}}
Include exactly 3 movies and 3 songs. "hue" is an integer 0-360 used for a CSS color."""

    response = model.generate_content(structured_prompt)
    text = response.text.strip()

    # Strip accidental markdown code fences if the model adds them anyway.
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.lower().startswith("json"):
            text = text[4:]

    data = json.loads(text)

    return data.get("reply", ""), data.get("movies", []), data.get("songs", [])


def generate_response(user_message: str, prompt: str = None, avoid_titles=None, avoid_genres=None):
    """
    Generate a chat reply plus structured movie/song recommendations.

    Returns
    -------
    (reply: str, movies: list[dict], songs: list[dict])
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        try:
            return _gemini_recommendations(user_message, prompt or user_message)
        except Exception as e:
            log.exception("Gemini request failed, falling back to mock recommendations")

    return _mock_recommendations(user_message, avoid_titles=avoid_titles, avoid_genres=avoid_genres)
