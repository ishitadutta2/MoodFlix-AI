"""
database/repositories/user_repository.py
---------------------------------------
User Repository
MoodFlix AI
"""

from database.db import users_collection
from database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def __init__(self):
        super().__init__(users_collection)

    def find_by_email(self, email: str):
        return self.find_one({"email": email.strip().lower()})

    def find_by_id(self, user_id):
        return self.find_one({"_id": user_id})

    def email_taken(self, email: str) -> bool:
        return self.exists({"email": email.strip().lower()})
