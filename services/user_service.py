"""
services/user_service.py
---------------------------------------
User auth orchestration (signup / login)
MoodFlix AI

auth_routes.py was still doing direct users_collection.find_one/
insert_one/update_one calls — this moves that into the services layer
like everything else, on top of the repository layer.
"""

from database.repositories import user_repo
from database.user_model import create_user, public_user
from services.auth_service import (
    hash_password,
    verify_password,
    validate_email,
    validate_password,
    is_locked,
    record_failed_login,
    record_successful_login,
)
from utils.logger import get_logger

log = get_logger("user_service")

MAX_EMAIL_LENGTH = 254
MAX_NAME_LENGTH = 100


def register_user(name: str, email: str, password: str):
    """Returns (user_doc, error_message, status_code)."""

    name = (name or "").strip()
    email = (email or "").strip().lower()

    if not name or not email or not password:
        return None, "All fields are required.", 400

    if len(name) > MAX_NAME_LENGTH:
        return None, f"Name must be under {MAX_NAME_LENGTH} characters.", 400

    if len(email) > MAX_EMAIL_LENGTH:
        return None, "Email address is too long.", 400

    if not validate_email(email):
        return None, "Please enter a valid email address.", 400

    password_ok, password_message = validate_password(password)
    if not password_ok:
        return None, password_message, 400

    if user_repo.email_taken(email):
        return None, "An account with that email already exists.", 409

    user_doc = create_user(name, email, hash_password(password))
    user_doc = user_repo.insert_one(user_doc)

    log.info(f"New signup: {email}")

    return user_doc, None, 200


def login_user(email: str, password: str):
    """Returns (user_doc, error_message, status_code)."""

    email = (email or "").strip().lower()

    if not email or not password:
        return None, "Email and password are required.", 400

    if not validate_email(email):
        return None, "Please enter a valid email address.", 400

    user = user_repo.find_by_email(email)

    if user and is_locked(user):
        log.warning(f"Login blocked (account locked): {email}")
        return None, "Too many failed attempts. Try again in a few minutes, or reset your password.", 423

    if not user or not verify_password(password, user.get("password", "")):
        if user:
            user_repo.update_one({"_id": user["_id"]}, {"$set": record_failed_login(user)})
            if user.get("failed_login_attempts", 0) + 1 >= 5:
                log.warning(f"Account locked after repeated failed logins: {email}")
        return None, "Invalid email or password.", 401

    user_repo.update_one({"_id": user["_id"]}, {"$set": record_successful_login()})
    log.info(f"Login success: {email}")

    return user, None, 200
