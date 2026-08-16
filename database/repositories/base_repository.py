"""
database/repositories/base_repository.py
---------------------------------------
Base Repository
MoodFlix AI

Repository layer sits between services and the raw Mongo (or mock)
collection objects in database/db.py:

    routes -> services -> repositories -> database/db.py (Mongo/mock)

This isolates "how do I query this collection" from "what does this
feature do", which makes services easier to unit test (swap a
repository for a fake/in-memory one) and keeps query shape changes
contained to one place per collection.
"""


class BaseRepository:

    def __init__(self, collection):
        self.collection = collection

    def find_one(self, query: dict):
        return self.collection.find_one(query)

    def find(self, query: dict = None):
        return list(self.collection.find(query or {}))

    def insert_one(self, document: dict):
        result = self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    def update_one(self, query: dict, update: dict):
        return self.collection.update_one(query, update)

    def delete_one(self, query: dict):
        return self.collection.delete_one(query)

    def delete_many(self, query: dict):
        for doc in self.find(query):
            self.collection.delete_one({"_id": doc["_id"]})

    def count(self, query: dict = None):
        return len(self.find(query))

    def exists(self, query: dict) -> bool:
        return self.find_one(query) is not None
