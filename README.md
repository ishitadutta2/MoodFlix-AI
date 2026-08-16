# MoodFlix AI

**v5.0.0**

A Flask app that recommends movies, songs, and more based on your mood — powered by Gemini (with a fully working mock mode if you don't have an API key).

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. No `.env` setup is required to try it — with no `MONGODB_URI` or `GEMINI_API_KEY` set, the app runs on an in-memory mock database and a deterministic mock recommender.

## Configuration

Copy `.env` and fill in what you have:

| Variable | Required? | Notes |
|---|---|---|
| `SECRET_KEY` | Recommended | Session signing key. Set a real one before deploying. |
| `MONGODB_URI` / `MONGODB_DB` | No | Leave blank to use the in-memory mock database. |
| `GEMINI_API_KEY` | No | Leave blank to use the mock recommender. |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | No | Leave blank and "sent" emails (password reset, verification) are logged to the console instead. |

## Architecture

```
routes/       → thin controllers (parse request, call a service, return JSON)
services/     → all business logic (validation, orchestration, caching)
database/
  repositories/ → one class per collection (find/insert/update/delete),
                  the only layer that talks to Mongo/mock collections
  *_model.py    → document shape + transforms (create_x / public_x)
  db.py         → Mongo connection + in-memory mock fallback
utils/        → auth decorators, CSRF, logging, shared helpers
templates/    → Jinja templates
static/       → CSS/JS, organized per-page
```

```
routes → services → repositories → database/db.py (Mongo or in-memory mock)
```

Repositories exist so services never write raw Mongo queries — `favorite_repo.find_by_user(...)` reads the same whether it's really Mongo or the mock, and it's the one place to change if a query needs to become an aggregation later. Services still own all the business logic (validation, caching, orchestrating multiple repositories); routes just parse the request and call one service function.

## What's new in v4

- **Repository layer** added between services and the database (see above) — including fixing `auth_routes.py`, which was still making direct DB calls after the v3 refactor.
- **Search everywhere**: chats, messages, favorites, and your saved genres/artists/actors are all searchable from one box. (Still no external movie/music catalog — nothing to search there without a TMDB/Spotify key.)
- **Notification and privacy settings** added to profile/settings (toggle switches, real persistence).
- **Chat upgrades**: markdown rendering (sanitized via DOMPurify), message timestamps, Share, and Continue (asks the model to expand its last reply in the same chat).
- **Mood Calendar**: a real feature, not a mockup — every day you've chatted gets an emoji for its dominant detected mood, click a day to revisit those chats. Built entirely from mood/timestamp data the app already tracked.
- Landing page: floating particle decorations and a subtle hero parallax effect (CSS/vanilla JS, no 3D library).
- Broader mobile responsiveness pass.

**Deliberately not built in this pass** (each is a substantial standalone feature — ask if you want one prioritized next): AI-generated 30-minute playlists, "Movie Night Mode" (group + snacks + pre/post playlists), a weekend activity planner, selectable AI personalities, daily challenges, and an achievement/badge system.

## What's new in v5

- **Sci-fi visual theme**: new dark-space palette (`#050816` background, purple/cyan/violet accents), glassmorphism, glowing hover states on buttons/cards, animated holographic borders on recommendation cards, an aurora background wash, and 300ms page-enter transitions.
- **Consistency pass**: equal-height card grids, a real spacing scale (`--space-sm/md/lg` = 12/24/32px) applied across dashboard/favorites/profile, 16–20px corner radii everywhere.
- **Loading states**: skeleton recommendation cards now show while the AI is generating a reply, not just the typing dots.
- Quick mood chips in chat (😊 😔 😌 😎), a circular mood meter + personalized time-of-day greeting on the dashboard, a recent-activity timeline sidebar.
- **Security headers** (CSP, X-Frame-Options, nosniff, etc.), **session idle timeout**, **Remember me**, **password strength meter**, real **MongoDB indexes** (incl. a TTL index that auto-expires password-reset/verification tokens), response **compression**.
- Favorites now support **folders/tags**, search/sort, and pagination at the API level (no frontend UI for folders yet — flagged below).
- Theme settings gained a **System** option that follows OS light/dark preference live.

**Known gaps from the latest request list, not yet built**: admin panel, achievement/streak system, profile data export (JSON/CSV), dashboard "recently viewed" and "because you liked X" sections, search autocomplete + recent-searches UI, mobile bottom navigation, a dedicated accessibility pass (ARIA labels/focus outlines), and expanded docs (CONTRIBUTING/LICENSE/API reference). Also unbuilt, same as before: real TMDB/Spotify integration and Google/GitHub OAuth login (need API keys/OAuth app credentials I don't have here), Cloudinary, and an actual live deployment. Happy to pick any of these up next — say which to prioritize.

### Notable design choices / honest limitations

- **No real email provider is configured.** `services/email_service.py` logs "sent" emails to the console with the real link inside, so password reset and email verification are fully functional in dev. Set `SMTP_*` env vars to send real email.
- **No external movie/music catalog (TMDB, Spotify, etc.) is wired in** — there's no API key for one. Recommendations come from Gemini (if configured) or a deterministic mock pool. "Trending" and "search" are scoped to your own data / the app's own users, not external charts.
- **Mood detection is keyword-based**, not a real sentiment model — see `services/mood_service.py` for the lexicon and its limits.
- **Chat "streaming"** (`/api/chat/stream`) reveals the finished reply word-by-word for a typing effect. The underlying recommendation is generated in one shot (both the mock recommender and Gemini's structured-JSON response need to be complete before anything is usable), so this isn't true token-by-token model streaming.
- **CSRF protection** uses a double-submit token (session token vs. `X-CSRF-Token` header), since the frontend is JSON/fetch-based rather than classic HTML forms. See `utils/csrf.py`.
- **Caching** is in-process (Flask-Caching `SimpleCache`) — fine for a single server. Swap to `RedisCache` in `extensions.py` if you scale to multiple workers/instances.

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Runs against the in-memory mock database — no MongoDB needed. CI runs this on every push (see `.github/workflows/ci.yml`).

## Deployment

**Docker Compose** (app + real MongoDB):
```bash
docker compose up --build
```

**Render / Railway / Heroku-style platforms**: a `Procfile` is included (`gunicorn -w 4 -b 0.0.0.0:$PORT app:app`). Set your env vars in the platform's dashboard.

**Manual**:
```bash
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

These deployment files are written correctly but untested against a live Docker daemon or hosting platform in this environment — sanity-check the first deploy.

## Feature overview

- Mood-based chat recommendations (movies, songs), with feedback ("Loved it" / "Not for me") that biases future suggestions
- Chat history: rename, delete, pin, search
- Favorites + Watch Later, across movies/songs/anime/TV shows/books
- Profile: avatar upload (validated & resized via Pillow), taste preferences, theme + accent color, streaming platforms
- Auth: signup/login, account lockout after 5 failed attempts, email verification, password reset — all via console-logged mock email by default
- Global search across your chats, messages, and favorites
- Analytics: chats this week, favorite genre, mood trend, recommendation acceptance rate, trending across all users
- Voice input, copy/regenerate/stop on chat replies (Chrome/Edge for voice; Web Speech API)
