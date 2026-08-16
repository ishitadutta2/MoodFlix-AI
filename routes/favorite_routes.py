"""
routes/favorite_routes.py
---------------------------------------
Favorite Routes
MoodFlix AI

Thin controllers only — logic lives in services/favorite_service.py.
"""

from flask import Blueprint, request, jsonify, g

from services import favorite_service
from services.cache_service import invalidate_dashboard
from utils.auth import login_required

favorite_routes = Blueprint("favorite_routes", __name__)


@favorite_routes.route("/api/favorites", methods=["GET"])
@login_required
def get_favorites():
    list_name = request.args.get("list")  # "favorites" | "watch_later" | None (all)
    folder = request.args.get("folder")
    search = request.args.get("search")
    sort = request.args.get("sort", "newest")

    favorites = favorite_service.list_favorites(
        str(g.current_user["_id"]), list_name=list_name, folder=folder, search=search, sort=sort
    )

    # Simple offset pagination (kept optional — omit page/per_page to get everything).
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)
    total = len(favorites)
    if page and per_page:
        start = (page - 1) * per_page
        favorites = favorites[start:start + per_page]

    return jsonify({
        "success": True,
        "favorites": favorites,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@favorite_routes.route("/api/favorites/folders", methods=["GET"])
@login_required
def get_folders():
    return jsonify({"success": True, "folders": favorite_service.list_folders(str(g.current_user["_id"]))})


@favorite_routes.route("/api/favorites/<favorite_id>/folder", methods=["PUT"])
@login_required
def move_favorite_folder(favorite_id):
    data = request.get_json(silent=True) or {}
    ok, error = favorite_service.move_to_folder(str(g.current_user["_id"]), favorite_id, data.get("folder", ""))
    if not ok:
        return jsonify({"success": False, "message": error}), 404
    return jsonify({"success": True, "message": "Moved."})


@favorite_routes.route("/api/favorites/bulk-delete", methods=["POST"])
@login_required
def bulk_delete_favorites():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"success": False, "message": "Provide a non-empty list of favorite ids."}), 400

    deleted = favorite_service.bulk_delete(str(g.current_user["_id"]), ids)
    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({"success": True, "message": f"Deleted {deleted} favorite(s).", "deleted": deleted})


@favorite_routes.route("/api/favorites", methods=["POST"])
@login_required
def add_favorite():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    favorite, error = favorite_service.add_favorite(str(g.current_user["_id"]), data)
    if error:
        return jsonify({"success": False, "message": error}), 400

    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({
        "success": True,
        "message": f"{favorite['title']} added.",
        "favorite": favorite,
    })


@favorite_routes.route("/api/favorites/<favorite_id>", methods=["DELETE"])
@login_required
def remove_favorite(favorite_id):
    ok, error = favorite_service.remove_favorite(str(g.current_user["_id"]), favorite_id)
    if not ok:
        return jsonify({"success": False, "message": error}), 404
    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({"success": True, "message": "Removed successfully."})


@favorite_routes.route("/api/favorites/movies", methods=["GET"])
@login_required
def favorite_movies():
    movies = favorite_service.list_favorites(str(g.current_user["_id"]), content_type="movie")
    return jsonify({"success": True, "movies": movies})


@favorite_routes.route("/api/favorites/songs", methods=["GET"])
@login_required
def favorite_songs():
    songs = favorite_service.list_favorites(str(g.current_user["_id"]), content_type="song")
    return jsonify({"success": True, "songs": songs})


@favorite_routes.route("/api/favorites", methods=["DELETE"])
@login_required
def clear_favorites():
    favorite_service.clear_favorites(str(g.current_user["_id"]))
    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({"success": True, "message": "All favorites removed."})


@favorite_routes.route("/api/trending", methods=["GET"])
def trending():
    # Public — no login required, this reflects aggregate activity across all users.
    return jsonify({"success": True, "trending": favorite_service.trending()})
