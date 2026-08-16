"""
tests/test_smoke.py
---------------------------------------
Smoke / integration tests for MoodFlix AI.

Run with: pytest
Uses the in-memory mock database (no MONGODB_URI needed).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

os.environ.setdefault("FLASK_ENV", "testing")

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def csrf_headers(client):
    token = client.get("/api/csrf-token").get_json()["csrf_token"]
    return {"X-CSRF-Token": token}


def signup(client, email="test@example.com", password="Passw0rd1", name="Test User"):
    return client.post("/api/signup", json={"name": name, "email": email, "password": password})


class TestPublicPages:
    def test_home_page(self, client):
        assert client.get("/").status_code == 200

    def test_login_page(self, client):
        assert client.get("/login").status_code == 200

    def test_signup_page(self, client):
        assert client.get("/signup").status_code == 200

    def test_404(self, client):
        assert client.get("/this-page-does-not-exist").status_code == 404


class TestAuth:
    def test_signup_success(self, client):
        r = signup(client)
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_signup_duplicate_email_rejected(self, client):
        signup(client, email="dupe@example.com")
        r = signup(client, email="dupe@example.com")
        assert r.status_code == 409

    def test_signup_weak_password_rejected(self, client):
        r = client.post("/api/signup", json={"name": "X", "email": "weak@example.com", "password": "weak"})
        assert r.status_code == 400

    def test_login_wrong_password(self, client):
        signup(client, email="wrongpw@example.com")
        client.post("/api/logout")
        r = client.post("/api/login", json={"email": "wrongpw@example.com", "password": "WrongPass1"})
        assert r.status_code == 401

    def test_account_lockout_after_five_failures(self, client):
        signup(client, email="lockout@example.com")
        client.post("/api/logout")
        for _ in range(5):
            client.post("/api/login", json={"email": "lockout@example.com", "password": "bad"})
        r = client.post("/api/login", json={"email": "lockout@example.com", "password": "Passw0rd1"})
        assert r.status_code == 423

    def test_dashboard_requires_login(self, client):
        r = client.get("/dashboard")
        assert r.status_code in (302, 401)


class TestCSRF:
    def test_mutating_request_without_token_rejected(self, client):
        signup(client, email="csrf@example.com")
        r = client.post("/api/chat", json={"message": "hi"})
        assert r.status_code == 403

    def test_mutating_request_with_token_allowed(self, client):
        signup(client, email="csrf2@example.com")
        r = client.post("/api/chat", json={"message": "hi"}, headers=csrf_headers(client))
        assert r.status_code == 200


class TestChat:
    def test_send_message_returns_recommendations(self, client):
        signup(client, email="chat@example.com")
        r = client.post("/api/chat", json={"message": "feeling nostalgic"}, headers=csrf_headers(client))
        data = r.get_json()
        assert r.status_code == 200
        assert data["success"] is True
        assert len(data["movies"]) == 3
        assert len(data["songs"]) == 3
        assert data["chat_id"]

    def test_chat_requires_login(self, client):
        r = client.post("/api/chat", json={"message": "hi"})
        assert r.status_code in (401, 403)


class TestFavorites:
    def test_add_and_list_favorite(self, client):
        signup(client, email="fav@example.com")
        H = csrf_headers(client)
        r = client.post("/api/favorites", json={"type": "movie", "title": "Spirited Away"}, headers=H)
        assert r.status_code == 200

        r = client.get("/api/favorites")
        favorites = r.get_json()["favorites"]
        assert any(f["title"] == "Spirited Away" for f in favorites)

    def test_cannot_delete_another_users_favorite(self, client):
        H = csrf_headers(client)
        signup(client, email="owner@example.com")
        r = client.post("/api/favorites", json={"type": "movie", "title": "Secret"}, headers=csrf_headers(client))
        fav_id = r.get_json()["favorite"]["id"]
        client.post("/api/logout")

        signup(client, email="attacker@example.com")
        r = client.delete(f"/api/favorites/{fav_id}", headers=csrf_headers(client))
        assert r.status_code == 404


class TestProfile:
    def test_update_profile(self, client):
        signup(client, email="profile@example.com")
        r = client.put("/api/profile", json={"name": "New Name"}, headers=csrf_headers(client))
        assert r.status_code == 200
        assert r.get_json()["profile"]["name"] == "New Name"

    def test_change_password_wrong_current(self, client):
        signup(client, email="pw@example.com")
        r = client.put(
            "/api/profile/password",
            json={"current_password": "WrongOne1", "new_password": "NewPassw0rd1"},
            headers=csrf_headers(client),
        )
        assert r.status_code == 401


class TestPasswordReset:
    def test_forgot_password_always_generic_response(self, client):
        r = client.post("/api/forgot-password", json={"email": "doesnotexist@example.com"}, headers=csrf_headers(client))
        assert r.status_code == 200
        assert r.get_json()["success"] is True


class TestSearchEverywhere:
    def test_search_matches_saved_genre(self, client):
        signup(client, email="searchgenre@example.com")
        H = csrf_headers(client)
        client.put("/api/profile", json={"favorite_genres": ["Sci-Fi"]}, headers=H)
        r = client.get("/api/search?q=sci")
        data = r.get_json()
        assert r.status_code == 200
        assert "Sci-Fi" in data["genres"]

    def test_search_requires_login(self, client):
        r = client.get("/api/search?q=test")
        assert r.status_code == 401


class TestMoodCalendar:
    def test_calendar_reflects_chat_mood(self, client):
        signup(client, email="calendartest@example.com")
        H = csrf_headers(client)
        r = client.post("/api/chat", json={"message": "feeling relaxed and calm tonight"}, headers=H)
        assert r.status_code == 200

        import datetime
        now = datetime.datetime.utcnow()
        r = client.get(f"/api/mood-calendar?year={now.year}&month={now.month}")
        assert r.status_code == 200
        today = next(d for d in r.get_json()["days"] if d["day"] == now.day)
        assert today["chat_count"] >= 1
        assert today["mood"] is not None

    def test_calendar_invalid_month_rejected(self, client):
        signup(client, email="calendarbad@example.com")
        r = client.get("/api/mood-calendar?year=2026&month=13")
        assert r.status_code == 400


class TestContinueChat:
    def test_continue_requires_existing_chat(self, client):
        signup(client, email="continuetest@example.com")
        H = csrf_headers(client)
        r = client.post("/api/chat", json={"message": "recommend something cozy"}, headers=H)
        chat_id = r.get_json()["chat_id"]

        r = client.post(f"/api/continue-chat/{chat_id}", headers=H)
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_continue_nonexistent_chat_404(self, client):
        signup(client, email="continue404@example.com")
        H = csrf_headers(client)
        r = client.post("/api/continue-chat/nonexistent-id", headers=H)
        assert r.status_code == 404
