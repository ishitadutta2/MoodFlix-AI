"""
routes/chat_routes.py
-------------------------------------
Chat API Routes
MoodFlix AI

Thin controllers only — all persistence/business logic lives in
services/chat_service.py.
"""

import json
import time

from flask import Blueprint, request, jsonify, g, Response, stream_with_context

from services import chat_service
from services.cache_service import invalidate_dashboard
from utils.auth import login_required
from utils.logger import get_logger

log = get_logger("chat_routes")

chat_routes = Blueprint("chat_routes", __name__)


# -----------------------------------------
# Send Message to AI
# -----------------------------------------
@chat_routes.route("/api/chat", methods=["POST"])
@login_required
def chat():

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    result, error = chat_service.send_message(
        g.current_user, data.get("message", ""), data.get("chat_id")
    )

    if error:
        status = 404 if error == "Chat not found." else 400
        return jsonify({"success": False, "message": error}), status

    invalidate_dashboard(str(g.current_user["_id"]))

    return jsonify({"success": True, **result})


# -----------------------------------------
# Send Message to AI (simulated streaming)
# -----------------------------------------
@chat_routes.route("/api/chat/stream", methods=["POST"])
@login_required
def chat_stream():
    """
    Server-Sent Events endpoint that reveals the reply progressively.

    Note: the underlying recommendation is generated in one shot (both
    the mock recommender and the structured-JSON Gemini call produce
    the full response before we have anything to send) — this endpoint
    streams that finished reply back word-by-word for a "typing" feel
    in the UI, it is not true token-by-token model streaming.
    """

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    result, error = chat_service.send_message(
        g.current_user, data.get("message", ""), data.get("chat_id")
    )

    if error:
        status = 404 if error == "Chat not found." else 400
        return jsonify({"success": False, "message": error}), status

    invalidate_dashboard(str(g.current_user["_id"]))

    def event_stream():
        words = result["reply"].split(" ")
        sent = ""
        for word in words:
            sent += (" " if sent else "") + word
            yield f"event: token\ndata: {json.dumps({'text': sent})}\n\n"
            time.sleep(0.02)

        final_payload = {
            "reply": result["reply"],
            "movies": result["movies"],
            "songs": result["songs"],
            "chat_id": result["chat_id"],
        }
        yield f"event: done\ndata: {json.dumps(final_payload)}\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


# -----------------------------------------
# Create New Chat
# -----------------------------------------
@chat_routes.route("/api/new-chat", methods=["POST"])
@login_required
def new_chat():

    data = request.get_json(silent=True) or {}
    chat = chat_service.create_new_chat(str(g.current_user["_id"]), data.get("title", ""))

    return jsonify({"success": True, "message": "New chat created.", "chat": chat})


# -----------------------------------------
# Get Chat History (legacy summary endpoint)
# -----------------------------------------
@chat_routes.route("/api/chat-history", methods=["GET"])
@login_required
def chat_history():
    history = chat_service.list_chats(str(g.current_user["_id"]))
    return jsonify({"success": True, "history": history})


# -----------------------------------------
# Delete Chat
# -----------------------------------------
@chat_routes.route("/api/delete-chat/<chat_id>", methods=["DELETE"])
@login_required
def delete_chat(chat_id):
    ok, error = chat_service.delete_chat(str(g.current_user["_id"]), chat_id)
    if not ok:
        return jsonify({"success": False, "message": error}), 404
    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({"success": True, "message": "Chat deleted."})


# -----------------------------------------
# Rename Chat
# -----------------------------------------
@chat_routes.route("/api/rename-chat/<chat_id>", methods=["PUT"])
@login_required
def rename_chat(chat_id):
    data = request.get_json(silent=True) or {}
    ok, error = chat_service.rename_chat(str(g.current_user["_id"]), chat_id, data.get("title", ""))
    if not ok:
        status = 404 if error == "Chat not found." else 400
        return jsonify({"success": False, "message": error}), status
    return jsonify({"success": True, "message": "Chat renamed successfully."})


# -----------------------------------------
# Pin / Unpin Chat
# -----------------------------------------
@chat_routes.route("/api/pin-chat/<chat_id>", methods=["PUT"])
@login_required
def pin_chat(chat_id):
    data = request.get_json(silent=True) or {}
    ok, error = chat_service.set_pinned(str(g.current_user["_id"]), chat_id, bool(data.get("pinned", True)))
    if not ok:
        return jsonify({"success": False, "message": error}), 404
    return jsonify({"success": True, "message": "Updated."})


# -----------------------------------------
# Continue previous reply
# -----------------------------------------
@chat_routes.route("/api/continue-chat/<chat_id>", methods=["POST"])
@login_required
def continue_chat(chat_id):
    result, error = chat_service.continue_reply(g.current_user, chat_id)
    if error:
        status = 404 if error == "Chat not found." else 400
        return jsonify({"success": False, "message": error}), status

    invalidate_dashboard(str(g.current_user["_id"]))
    return jsonify({"success": True, **result})
