"""
database/repositories/__init__.py

Shared repository singletons. Services should import from here rather
than instantiating repositories themselves, e.g.:

    from database.repositories import user_repo, chat_repo
"""

from database.repositories.user_repository import UserRepository
from database.repositories.chat_repository import ChatRepository
from database.repositories.message_repository import MessageRepository
from database.repositories.favorite_repository import FavoriteRepository
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.token_repository import TokenRepository

user_repo = UserRepository()
chat_repo = ChatRepository()
message_repo = MessageRepository()
favorite_repo = FavoriteRepository()
feedback_repo = FeedbackRepository()
token_repo = TokenRepository()

__all__ = [
    "UserRepository", "ChatRepository", "MessageRepository",
    "FavoriteRepository", "FeedbackRepository", "TokenRepository",
    "user_repo", "chat_repo", "message_repo", "favorite_repo", "feedback_repo", "token_repo",
]
