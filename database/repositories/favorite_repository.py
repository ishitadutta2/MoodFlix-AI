"""
database/repositories/favorite_repository.py
---------------------------------------
Favorite Repository
MoodFlix AI
"""

from database.db import favorites_collection
from database.repositories.base_repository import BaseRepository


class FavoriteRepository(BaseRepository):

    def __init__(self):
        super().__init__(favorites_collection)

    def find_by_user(self, user_id: str, list_name: str = None, content_type: str = None):
        query = {"user_id": user_id}
        if list_name:
            query["list"] = list_name
        if content_type:
            query["content_type"] = content_type
        return self.find(query)

    def find_owned(self, favorite_id, user_id: str):
        favorite = self.find_one({"_id": favorite_id})
        if not favorite or favorite.get("user_id") != user_id:
            return None
        return favorite

    def delete_all_for_user(self, user_id: str, list_name: str = None):
        self.delete_many(self._user_query(user_id, list_name))

    def _user_query(self, user_id, list_name):
        query = {"user_id": user_id}
        if list_name:
            query["list"] = list_name
        return query
