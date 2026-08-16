"""
database/ids.py
---------------------------------------
ID helpers
MoodFlix AI

MongoDB uses ObjectId for _id, but the in-memory mock database
(used when no MONGODB_URI is configured) uses plain strings.
These helpers let route code work with either backend without
caring which one is active.
"""

from bson.objectid import ObjectId
from bson.errors import InvalidId


def parse_id(raw_id):
    """
    Convert a string id into an ObjectId when it's valid Mongo
    ObjectId format; otherwise return it unchanged (mock DB ids).
    """

    if raw_id is None:
        return None

    try:
        return ObjectId(raw_id)
    except (InvalidId, TypeError):
        return raw_id


def stringify(value):
    """Safe str() for ids that may already be strings or ObjectIds."""

    if value is None:
        return None

    return str(value)
