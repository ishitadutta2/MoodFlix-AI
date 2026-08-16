"""
database/repositories/chat_repository.py
---------------------------------------
Chat Repository
MoodFlix AI
"""

from database.db import chats_collection
from database.repositories.base_repository import BaseRepository


class ChatRepository(BaseRepository):

    def __init__(self):
        super().__init__(chats_collection)

    def find_by_user(self, user_id: str):
        return self.find({"user_id": user_id})

    def find_owned(self, chat_id, user_id: str):
        chat = self.find_one({"_id": chat_id})
        if not chat or chat.get("user_id") != user_id:
            return None
        return chat

    def delete_all_for_user(self, user_id: str):
        chats = self.find_by_user(user_id)
        for chat in chats:
            self.delete_one({"_id": chat["_id"]})
        return len(chats)
