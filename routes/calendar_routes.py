"""
routes/calendar_routes.py
---------------------------------------
Mood Calendar Routes
MoodFlix AI
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from services import calendar_service
from utils.auth import login_required

calendar_routes = Blueprint("calendar_routes", __name__)


@calendar_routes.route("/api/mood-calendar", methods=["GET"])
@login_required
def month_calendar():
    now = datetime.utcnow()
    try:
        year = int(request.args.get("year", now.year))
        month = int(request.args.get("month", now.month))
    except ValueError:
        return jsonify({"success": False, "message": "Invalid year/month."}), 400

    if not (1 <= month <= 12):
        return jsonify({"success": False, "message": "Month must be between 1 and 12."}), 400

    data = calendar_service.get_month_calendar(str(g.current_user["_id"]), year, month)
    return jsonify({"success": True, "year": year, "month": month, **data})


@calendar_routes.route("/api/mood-calendar/day/<date_str>", methods=["GET"])
@login_required
def day_detail(date_str):
    chats = calendar_service.get_day_detail(str(g.current_user["_id"]), date_str)
    if chats is None:
        return jsonify({"success": False, "message": "Invalid date format, expected YYYY-MM-DD."}), 400

    return jsonify({"success": True, "date": date_str, "chats": chats})
