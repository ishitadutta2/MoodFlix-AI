"""
database/repositories/token_repository.py
---------------------------------------
Token Repository
MoodFlix AI
"""

from database.db import tokens_collection
from database.repositories.base_repository import BaseRepository
from database.token_model import find_valid_token


class TokenRepository(BaseRepository):

    def __init__(self):
        super().__init__(tokens_collection)

    def find_valid(self, raw_token: str, purpose: str):
        return find_valid_token(self.collection, raw_token, purpose)

    def mark_used(self, token_id):
        self.update_one({"_id": token_id}, {"$set": {"used": True}})
