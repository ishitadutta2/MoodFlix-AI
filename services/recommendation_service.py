"""
services/recommendation_service.py
--------------------------------------------------
Recommendation Service
MoodFlix AI

Creates personalized prompts for Gemini (or the mock recommender).
"""

from services.gemini_service import generate_response


def recommend_content(
    message,
    mood="",
    genres=None,
    languages=None,
    artists=None,
    actors=None,
    previous_likes=None,
    disliked_genres=None,
    disliked_titles=None,
):
    """
    Generate personalized recommendations.

    Parameters
    ----------
    message : str
        User's latest message.
    mood : str
        Detected/current mood.
    genres, languages, artists, actors : list[str]
        Stored taste preferences from the user's profile.
    previous_likes : list[str]
        Previously liked recommendations (favorites + "Loved it" feedback).
    disliked_genres, disliked_titles : list[str]
        From "Not for me" feedback — the engine should avoid these.
    """

    genres = genres or []
    languages = languages or []
    artists = artists or []
    actors = actors or []
    previous_likes = previous_likes or []
    disliked_genres = disliked_genres or []
    disliked_titles = disliked_titles or []

    prompt = f"""
You are MoodFlix AI.

Your goal is to recommend entertainment that matches the user's preferences.

User Profile

Mood:
{mood or "Unknown"}

Favorite Genres:
{', '.join(genres) if genres else "Unknown"}

Preferred Languages:
{', '.join(languages) if languages else "Unknown"}

Favorite Artists:
{', '.join(artists) if artists else "Unknown"}

Favorite Actors:
{', '.join(actors) if actors else "Unknown"}

Previously Liked:
{', '.join(previous_likes) if previous_likes else "None"}

Genres to avoid (user marked these "Not for me"):
{', '.join(disliked_genres) if disliked_genres else "None"}

Titles already shown and rejected (do not repeat):
{', '.join(disliked_titles) if disliked_titles else "None"}

Current User Request:
{message}

Instructions:

- Recommend 3 movies.
- Recommend 3 songs.
- Recommend anime if appropriate.
- Explain why each recommendation matches.
- Include recommendations from different countries when suitable.
- Keep the tone friendly.
- Avoid recommending the same title repeatedly.
- Never recommend a title from the "already shown and rejected" list above.
"""

    return generate_response(
        message,
        prompt=prompt,
        avoid_titles=disliked_titles,
        avoid_genres=disliked_genres,
    )
