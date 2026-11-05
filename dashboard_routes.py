from datetime import datetime
from flask import Blueprint, render_template, session, jsonify, g
from bson import ObjectId
from app.database import get_db
from app.routes.auth_routes import login_required
from app.models.event_model import EventModel
from app.models.notification_model import NotificationModel

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def home():
    if session.get("user_id"):
        return render_template("dashboard/redirect.html")
    return render_template("auth/login.html")

@dashboard_bp.route("/dashboard")
@login_required
def index():
    db = get_db()
    user_id = ObjectId(session["user_id"])
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Fetch all user events
    all_events = list(db.events.find({"user_id": user_id}).sort("event_date", 1))
    
    # Compute dynamic statistics from MongoDB
    total_events = len(all_events)
    upcoming_events = [e for e in all_events if e.get("event_date", "") >= today_str]
    past_events = [e for e in all_events if e.get("event_date", "") < today_str]
    
    safe_events = [e for e in all_events if e.get("weather_risk", {}).get("risk_level") == "Low Risk"]
    moderate_events = [e for e in all_events if e.get("weather_risk", {}).get("risk_level") == "Moderate Risk"]
    high_risk_events = [e for e in all_events if e.get("weather_risk", {}).get("risk_level") == "High Risk"]
    unverified_events = [e for e in all_events if e.get("weather_risk", {}).get("risk_level") in ("Beyond Forecast Horizon", "Pending Analysis")]

    rainout_alerts = [e for e in all_events if e.get("weather_risk", {}).get("rainout_risk") == "High Risk"]
    heat_alerts = [e for e in all_events if e.get("weather_risk", {}).get("heat_risk") == "High Risk"]

    # Category distribution
    categories = {}
    for ev in all_events:
        cat = ev.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    # Recent notifications
    recent_notifs = NotificationModel.get_user_notifications(user_id, limit=5)

    stats = {
        "total_events": total_events,
        "upcoming_count": len(upcoming_events),
        "past_count": len(past_events),
        "safe_count": len(safe_events),
        "moderate_count": len(moderate_events),
        "high_risk_count": len(high_risk_events),
        "unverified_count": len(unverified_events),
        "rainout_alerts_count": len(rainout_alerts),
        "heat_alerts_count": len(heat_alerts),
    }

    return render_template(
        "dashboard/index.html",
        stats=stats,
        upcoming_events=upcoming_events[:6],
        high_risk_events=high_risk_events,
        recent_notifs=recent_notifs,
        categories=categories
    )

@dashboard_bp.route("/dashboard/api/chart-data")
@login_required
def chart_data():
    db = get_db()
    user_id = ObjectId(session["user_id"])
    events = list(db.events.find({"user_id": user_id}))

    # Risk counts
    risk_counts = {
        "Low Risk": 0,
        "Moderate Risk": 0,
        "High Risk": 0,
        "Beyond Horizon / Pending": 0
    }
    for e in events:
        lvl = e.get("weather_risk", {}).get("risk_level", "Pending Analysis")
        if lvl in risk_counts:
            risk_counts[lvl] += 1
        else:
            risk_counts["Beyond Horizon / Pending"] += 1

    # Category breakdown
    cat_counts = {}
    for e in events:
        c = e.get("category", "Other")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    # Upcoming 7-day timeline risks
    upcoming = sorted([e for e in events if e.get("event_date")], key=lambda x: x["event_date"])[:7]
    timeline = [{
        "name": e["name"],
        "date": e["event_date"],
        "safety_score": e.get("weather_risk", {}).get("safety_score", 50) or 50,
        "risk": e.get("weather_risk", {}).get("risk_level", "Pending")
    } for e in upcoming]

    return jsonify({
        "risk_breakdown": risk_counts,
        "category_breakdown": cat_counts,
        "timeline": timeline
    })

