"""
database/db.py
---------------------------------------
MongoDB Connection
MoodFlix AI

If MONGODB_URI is not set (or the connection fails), the app falls
back to a lightweight in-memory mock database instead of crashing,
exactly as the .env template promises ("leave blank to use
in-memory mock data instead").
"""

import os
import itertools

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()


# ==================================================
# In-memory mock collection (used when Mongo is not
# configured / not reachable, so local dev still works)
# ==================================================
class MockCollection:
    def __init__(self):
        self._docs = {}
        self._counter = itertools.count(1)

    def insert_one(self, doc):
        doc = dict(doc)
        doc["_id"] = doc.get("_id") or str(next(self._counter))
        self._docs[doc["_id"]] = doc

        class _Result:
            inserted_id = doc["_id"]

        return _Result()

    def find_one(self, query=None):
        query = query or {}
        for doc in self._docs.values():
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find(self, query=None):
        query = query or {}
        return [
            doc for doc in self._docs.values()
            if all(doc.get(k) == v for k, v in query.items())
        ]

    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc:
            for k, v in update.get("$set", {}).items():
                doc[k] = v

    def delete_one(self, query):
        doc = self.find_one(query)
        if doc:
            del self._docs[doc["_id"]]


class MockDB:
    def __init__(self):
        self._collections = {}

    def __getitem__(self, name):
        if name not in self._collections:
            self._collections[name] = MockCollection()
        return self._collections[name]


class MongoDB:

    def __init__(self):

        self.client = None
        self.db = None

        self.connect()

    def connect(self):

        mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")

        if not mongo_uri:
            print("⚠️  MONGODB_URI not set — using in-memory mock database.")
            self.db = MockDB()
            return

        try:

            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

            # Check connection
            self.client.admin.command("ping")

            db_name = os.getenv("MONGODB_DB", "MoodFlixAI")
            self.db = self.client[db_name]

            print("✅ MongoDB Connected Successfully")

            self._ensure_indexes(self.db)

        except PyMongoError as e:

            print("❌ MongoDB Connection Failed — falling back to in-memory mock database.")
            print(e)
            self.client = None
            self.db = MockDB()

    def get_database(self):
        return self.db

    @staticmethod
    def _ensure_indexes(db):
        """
        Real indexes — only meaningful against a real Mongo instance
        (the in-memory mock doesn't need them; every query there is
        already a Python list scan). Safe to call on every startup:
        create_index is a no-op if the index already exists.
        """
        try:
            db["users"].create_index("email", unique=True)
            db["chats"].create_index("user_id")
            db["chats"].create_index([("user_id", 1), ("updated_at", -1)])
            db["messages"].create_index("chat_id")
            db["favorites"].create_index([("user_id", 1), ("list", 1), ("content_type", 1)])
            db["feedback"].create_index("user_id")
            db["tokens"].create_index("token_hash")
            db["tokens"].create_index("expires_at", expireAfterSeconds=0)
        except Exception as e:
            print(f"⚠️  Could not create indexes: {e}")


# Create one database instance
mongodb = MongoDB()

db = mongodb.get_database()


# ==================================================
# Collections
# ==================================================

users_collection = db["users"]

preferences_collection = db["preferences"]

chats_collection = db["chats"]

messages_collection = db["messages"]

favorites_collection = db["favorites"]

feedback_collection = db["feedback"]

tokens_collection = db["tokens"]
