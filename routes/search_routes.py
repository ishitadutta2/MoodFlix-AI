"""
routes/search_routes.py
---------------------------------------
Global Search Routes
MoodFlix AI
"""

from flask import Blueprint, request, jsonify, g

from services import search_service
from utils.auth import login_required

search_routes = Blueprint("search_routes", __name__)


@search_routes.route("/api/search", methods=["GET"])
@login_required
def search():
    query = request.args.get("q", "")
    results = search_service.search(str(g.current_user["_id"]), query, user=g.current_user)
    return jsonify({"success": True, "query": query, **results})
