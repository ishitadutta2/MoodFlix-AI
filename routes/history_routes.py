"""
routes/history_routes.py
---------------------------------------
Chat History Routes
MoodFlix AI

Thin controllers only — logic lives in services/chat_service.py
(shared with routes/chat_routes.py so it isn't duplicated).
"""

from flask import Blueprint, jsonify, request, g

from services import chat_service
from services.cache_service import invalidate_dashboard
from utils.auth import login_required

history_routes = Blueprint("history_routes", __name__)


@history_routes.route("/api/history", methods=["GET"])
@login_required
def get_history():
    return jsonify({"success": True, "history": chat_service.list_chats(str(g.current_user["_id"]))})


@history_routes.route("/api/history/<chat_id>", methods=["GET"])
@login_required
def get_chat(chat_id):
    chat, messages, error = chat_service.get_chat(str(g.current_user["_id"]), chat_id)
    if error:
        return jsonify({"success": False, "message": error}), 404
    return jsonify({"success": True, "chat": chat, "messages": messages})


@history_routes.route("/api/history/<chat_id>", methods=["DELETE"])
@login_required
def delete_chat(chat_id):
    ok, error = chat_service.delete_chat(str(g.current_user["_id"]), chat_id)
    if not ok:
        return jsonify({"success": False, "message": error}), 404
    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({"success": True, "message": "Chat deleted successfully."})


@history_routes.route("/api/history", methods=["DELETE"])
@login_required
def delete_all_chats():
    count = chat_service.delete_all_chats(str(g.current_user["_id"]))
    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({"success": True, "message": f"Deleted {count} chat(s)."})


@history_routes.route("/api/history/<chat_id>", methods=["PUT"])
@login_required
def rename_chat(chat_id):
    data = request.get_json(silent=True) or {}
    ok, error = chat_service.rename_chat(str(g.current_user["_id"]), chat_id, data.get("title", ""))
    if not ok:
        status = 404 if error == "Chat not found." else 400
        return jsonify({"success": False, "message": error}), status
    return jsonify({"success": True, "message": "Chat renamed."})


@history_routes.route("/api/history/<chat_id>/pin", methods=["PUT"])
@login_required
def pin_chat(chat_id):
    data = request.get_json(silent=True) or {}
    ok, error = chat_service.set_pinned(str(g.current_user["_id"]), chat_id, bool(data.get("pinned", True)))
    if not ok:
        return jsonify({"success": False, "message": error}), 404
    return jsonify({"success": True, "message": "Updated."})


@history_routes.route("/api/history/search/<keyword>", methods=["GET"])
@login_required
def search_history(keyword):
    results = chat_service.search_chats(str(g.current_user["_id"]), keyword)
    return jsonify({"success": True, "keyword": keyword, "results": results})
