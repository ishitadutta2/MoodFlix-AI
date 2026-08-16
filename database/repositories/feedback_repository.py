"""
database/repositories/feedback_repository.py
---------------------------------------
Feedback Repository
MoodFlix AI
"""

from database.db import feedback_collection
from database.repositories.base_repository import BaseRepository


class FeedbackRepository(BaseRepository):

    def __init__(self):
        super().__init__(feedback_collection)

    def find_by_user(self, user_id: str, reaction: str = None):
        query = {"user_id": user_id}
        if reaction:
            query["reaction"] = reaction
        return self.find(query)
