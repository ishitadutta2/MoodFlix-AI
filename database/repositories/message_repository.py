"""
database/repositories/message_repository.py
---------------------------------------
Message Repository
MoodFlix AI
"""

from database.db import messages_collection
from database.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository):

    def __init__(self):
        super().__init__(messages_collection)

    def find_by_chat(self, chat_id: str):
        return self.find({"chat_id": chat_id})

    def delete_by_chat(self, chat_id: str):
        self.delete_many({"chat_id": chat_id})

    def search_text(self, chat_ids: set, keyword_lower: str, limit: int = 20):
        """
        Full scan + Python-side filter — the mock DB backend doesn't
        support text/regex queries, so this keeps both backends
        consistent. Fine at this app's scale; swap for a real text
        index if message volume grows.
        """
        matches = []
        for m in self.find({}):
            if m.get("chat_id") in chat_ids and keyword_lower in (m.get("message") or "").lower():
                matches.append(m)
                if len(matches) >= limit:
                    break
        return matches
