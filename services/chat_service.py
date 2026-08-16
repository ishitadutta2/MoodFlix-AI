"""
services/chat_service.py
---------------------------------------
Chat / History Service
MoodFlix AI

Both routes/chat_routes.py (the active chat UI) and
routes/history_routes.py (the history management page) delegate here,
so the chat/message persistence logic exists in exactly one place.
"""

from database.repositories import chat_repo, message_repo, favorite_repo
from database.chat_model import create_chat, create_message, public_chat, public_message, update_chat
from database.history_model import history_response
from database.ids import parse_id
from services.recommendation_service import recommend_content
from services.mood_service import detect_mood
from services import feedback_service
from utils.logger import get_logger

log = get_logger("chat_service")

MAX_MESSAGE_LENGTH = 2000
MAX_TITLE_LENGTH = 120


def send_message(user: dict, message: str, chat_id: str = None):
    """
    Persist a user message, generate a recommendation, persist the
    assistant's reply, and update the parent chat.

    Returns (result_dict, error_message). result_dict has:
    reply, movies, songs, chat_id, mood
    """

    message = (message or "").strip()

    if not message:
        return None, "Message cannot be empty."

    if len(message) > MAX_MESSAGE_LENGTH:
        return None, f"Message must be under {MAX_MESSAGE_LENGTH} characters."

    user_id = str(user.get("_id"))

    chat_doc = None
    if chat_id:
        chat_doc = chat_repo.find_owned(parse_id(chat_id), user_id)
        if not chat_doc:
            return None, "Chat not found."

    if not chat_doc:
        title = message[:40] + ("…" if len(message) > 40 else "")
        chat_doc = chat_repo.insert_one(create_chat(user_id, title=title or "New Chat"))

    mood = detect_mood(message)

    # Favorites + "loved" feedback both count as positive signal for the prompt.
    favorite_titles = [f.get("title") for f in favorite_repo.find_by_user(user_id) if f.get("title")]
    signals = feedback_service.get_signals(user_id)
    previous_likes = list(set(favorite_titles + signals["loved_titles"]))

    try:
        reply, movies, songs = recommend_content(
            message=message,
            mood=mood,
            genres=user.get("favorite_genres"),
            languages=user.get("favorite_languages"),
            artists=user.get("favorite_artists"),
            actors=user.get("favorite_actors"),
            previous_likes=previous_likes,
            disliked_genres=signals["disliked_genres"],
            disliked_titles=signals["disliked_titles"],
        )
    except Exception:
        log.exception(f"Recommendation generation failed for user={user_id}")
        return None, "Couldn't generate a recommendation right now. Please try again."

    user_message = create_message(str(chat_doc["_id"]), "user", message, mood=mood)
    message_repo.insert_one(user_message)

    ai_message = create_message(str(chat_doc["_id"]), "assistant", reply)
    ai_message["movies"] = movies
    ai_message["songs"] = songs
    message_repo.insert_one(ai_message)

    updated_chat = update_chat(chat_doc, reply, mood=mood)
    chat_repo.update_one(
        {"_id": chat_doc["_id"]},
        {"$set": {
            "last_message": updated_chat["last_message"],
            "message_count": updated_chat["message_count"],
            "mood": updated_chat["mood"],
            "updated_at": updated_chat["updated_at"],
        }},
    )

    return {
        "reply": reply,
        "movies": movies,
        "songs": songs,
        "chat_id": str(chat_doc["_id"]),
        "mood": mood,
    }, None


def create_new_chat(user_id: str, title: str = ""):
    title = (title or "").strip()[:MAX_TITLE_LENGTH] or "New Chat"
    chat_doc = chat_repo.insert_one(create_chat(user_id, title=title))
    return public_chat(chat_doc)


def list_chats(user_id: str):
    chats = chat_repo.find_by_user(user_id)
    # Pinned chats first, then most recently updated.
    chats.sort(key=lambda c: (not c.get("pinned", False), -(c.get("updated_at") or c.get("created_at")).timestamp()))
    return history_response(chats)


def get_chat(user_id: str, chat_id: str):
    """Returns (chat_dict, messages_list, error_message)."""

    chat_doc = chat_repo.find_owned(parse_id(chat_id), user_id)
    if not chat_doc:
        return None, None, "Chat not found."

    messages = message_repo.find_by_chat(str(chat_doc["_id"]))
    return public_chat(chat_doc), [public_message(m) for m in messages], None


def delete_chat(user_id: str, chat_id: str):
    chat_doc = chat_repo.find_owned(parse_id(chat_id), user_id)
    if not chat_doc:
        return False, "Chat not found."

    message_repo.delete_by_chat(str(chat_doc["_id"]))
    chat_repo.delete_one({"_id": chat_doc["_id"]})
    return True, None


def delete_all_chats(user_id: str):
    chats = chat_repo.find_by_user(user_id)
    for chat_doc in chats:
        message_repo.delete_by_chat(str(chat_doc["_id"]))
        chat_repo.delete_one({"_id": chat_doc["_id"]})
    return len(chats)


def rename_chat(user_id: str, chat_id: str, title: str):
    title = (title or "").strip()

    if not title:
        return False, "Title cannot be empty."
    if len(title) > MAX_TITLE_LENGTH:
        return False, f"Title must be under {MAX_TITLE_LENGTH} characters."

    chat_doc = chat_repo.find_owned(parse_id(chat_id), user_id)
    if not chat_doc:
        return False, "Chat not found."

    chat_repo.update_one({"_id": chat_doc["_id"]}, {"$set": {"title": title}})
    return True, None


def set_pinned(user_id: str, chat_id: str, pinned: bool):
    chat_doc = chat_repo.find_owned(parse_id(chat_id), user_id)
    if not chat_doc:
        return False, "Chat not found."

    chat_repo.update_one({"_id": chat_doc["_id"]}, {"$set": {"pinned": bool(pinned)}})
    return True, None


def search_chats(user_id: str, keyword: str):
    keyword_lower = (keyword or "").strip().lower()
    chats = chat_repo.find_by_user(user_id)
    matches = [
        c for c in chats
        if keyword_lower in (c.get("title") or "").lower()
        or keyword_lower in (c.get("last_message") or "").lower()
    ]
    return history_response(matches)


def total_chats(user_id: str):
    return chat_repo.count({"user_id": user_id})


def continue_reply(user: dict, chat_id: str):
    """
    "Continue" — asks the model to expand on its own previous reply in
    the same chat, rather than responding to a new user message.
    """

    chat_doc = chat_repo.find_owned(parse_id(chat_id), str(user.get("_id")))
    if not chat_doc:
        return None, "Chat not found."

    messages = message_repo.find_by_chat(str(chat_doc["_id"]))
    last_assistant = next((m for m in reversed(messages) if m.get("sender") == "assistant"), None)

    if not last_assistant:
        return None, "There's nothing to continue yet — send a message first."

    continue_prompt = (
        f"Continue and expand on your previous response: \"{last_assistant.get('message', '')[:300]}\". "
        "Add more detail or a couple more suggestions in the same spirit."
    )

    return send_message(user, continue_prompt, str(chat_doc["_id"]))
