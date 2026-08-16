"""
database/chat_model.py
---------------------------------------
Chat Model
MoodFlix AI
"""

from datetime import datetime


# =====================================================
# Chat Document
# =====================================================

def create_chat(user_id: str, title: str = "New Chat"):
    """
    Create a new chat document.
    """

    return {
        "user_id": user_id,

        "title": title,

        "last_message": "",

        "message_count": 0,

        "pinned": False,

        "mood": None,

        "created_at": datetime.utcnow(),

        "updated_at": datetime.utcnow()
    }


# =====================================================
# Message Document
# =====================================================

def create_message(
    chat_id: str,
    sender: str,
    message: str,
    mood: str = None,
):
    """
    Create a chat message.

    sender:
        user
        assistant
    """

    return {

        "chat_id": chat_id,

        "sender": sender,

        "message": message,

        "mood": mood,

        "created_at": datetime.utcnow()
    }


# =====================================================
# Public Chat
# =====================================================

def public_chat(chat):

    if not chat:
        return None

    return {

        "id": str(chat.get("_id")),

        "title": chat.get("title"),

        "last_message": chat.get("last_message"),

        "message_count": chat.get("message_count"),

        "pinned": chat.get("pinned", False),

        "mood": chat.get("mood"),

        "created_at": chat.get("created_at"),

        "updated_at": chat.get("updated_at")
    }


# =====================================================
# Public Message
# =====================================================

def public_message(message):

    if not message:
        return None

    return {

        "id": str(message.get("_id")),

        "chat_id": str(message.get("chat_id")),

        "sender": message.get("sender"),

        "message": message.get("message"),

        "mood": message.get("mood"),

        "movies": message.get("movies", []),

        "songs": message.get("songs", []),

        "created_at": message.get("created_at")
    }


# =====================================================
# Update Chat
# =====================================================

def update_chat(chat, last_message, mood=None):

    chat["last_message"] = last_message

    chat["message_count"] += 1

    if mood:
        chat["mood"] = mood

    chat["updated_at"] = datetime.utcnow()

    return chat
