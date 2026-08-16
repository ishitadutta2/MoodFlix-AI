"""
database/history_model.py
---------------------------------------
History Helper Model
MoodFlix AI

Note:
Chat history is stored in the "chats" and "messages"
collections. This file contains helper functions for
returning history to the frontend.
"""


def history_item(chat: dict):
    """
    Convert a chat document into the format
    expected by the History page.
    """

    if not chat:
        return None

    return {
        "id": str(chat.get("_id")),
        "title": chat.get("title"),
        "last_message": chat.get("last_message"),
        "message_count": chat.get("message_count"),
        "pinned": chat.get("pinned", False),
        "mood": chat.get("mood"),
        "updated_at": chat.get("updated_at"),
    }


def history_response(chats):
    """
    Format a list of chat documents.
    """

    return [history_item(chat) for chat in chats]