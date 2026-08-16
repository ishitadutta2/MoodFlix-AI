from flask import Blueprint, render_template, redirect, url_for, g, request

from database.user_model import public_user
from utils.auth import login_required_page, get_current_user
from utils.colors import hue_for
from services import chat_service, dashboard_service, analytics_service


page_routes = Blueprint("page_routes", __name__)


@page_routes.route("/")
def home():
    stats = analytics_service.get_platform_stats()
    return render_template("index.html", **stats)


@page_routes.route("/login")
def login():
    if get_current_user():
        return redirect(url_for("page_routes.dashboard"))
    return render_template("login.html")


@page_routes.route("/signup")
def signup():
    if get_current_user():
        return redirect(url_for("page_routes.dashboard"))
    return render_template("signup.html")


@page_routes.route("/dashboard")
@login_required_page
def dashboard():
    data = dashboard_service.get_dashboard_data(g.current_user)
    return render_template("dashboard.html", **data)


@page_routes.route("/chatbot")
def chatbot():
    # Chat is browsable as a demo without logging in; sending a message
    # still requires auth (enforced by the /api/chat endpoint).
    user = get_current_user()

    chat = None
    initial_messages = []

    chat_id = request.args.get("chat_id")
    if user and chat_id:
        chat, messages, error = chat_service.get_chat(str(user["_id"]), chat_id)
        if not error:
            for m in messages:
                m["movies"] = [{**mv, "hue": mv.get("hue") or hue_for(mv.get("title", ""))} for mv in m.get("movies", [])]
                m["songs"] = [{**sg, "hue": sg.get("hue") or hue_for(sg.get("title", ""))} for sg in m.get("songs", [])]
            initial_messages = messages
        else:
            chat = None

    return render_template(
        "chatbot.html",
        user=public_user(user) if user else None,
        chat=chat,
        initial_messages=initial_messages,
        active_page="chatbot",
    )


@page_routes.route("/history")
@login_required_page
def history():
    return render_template("history.html", user=public_user(g.current_user), active_page="history")


@page_routes.route("/favorites")
@login_required_page
def favorites():
    return render_template("favorites.html", user=public_user(g.current_user), active_page="favorites")


@page_routes.route("/about")
def about():
    return render_template("about.html")


@page_routes.route("/contact")
def contact():
    return render_template("contact.html")


@page_routes.route("/profile")
@login_required_page
def profile():
    return render_template("profile.html", user=public_user(g.current_user), active_page="profile")


@page_routes.route("/settings")
@login_required_page
def settings():
    return render_template("settings.html", user=public_user(g.current_user), active_page="settings")


@page_routes.route("/search")
@login_required_page
def search():
    return render_template("search.html", user=public_user(g.current_user), active_page="search")


@page_routes.route("/analytics")
@login_required_page
def analytics():
    return render_template("analytics.html", user=public_user(g.current_user), active_page="analytics")


@page_routes.route("/mood-calendar")
@login_required_page
def mood_calendar():
    return render_template("mood_calendar.html", user=public_user(g.current_user), active_page="mood_calendar")


@page_routes.app_errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404
