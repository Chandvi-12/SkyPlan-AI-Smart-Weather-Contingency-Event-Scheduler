from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bson import ObjectId
from app.routes.auth_routes import login_required
from app.models.event_model import EventModel, VALID_CATEGORIES
from app.models.prediction_model import PredictionModel
from app.models.venue_model import VenueModel
from app.services.risk_analyzer import RiskAnalyzer

event_bp = Blueprint("events", __name__, url_prefix="/events")

@event_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    category = request.args.get("category", "all")
    risk_level = request.args.get("risk_level", "all")
    search_q = request.args.get("q", "").strip()

    events = EventModel.list_by_user(
        user_id=user_id,
        category=category if category != "all" else None,
        risk_level=risk_level if risk_level != "all" else None,
        search_query=search_q if search_q else None
    )

    return render_template(
        "events/index.html",
        events=events,
        categories=VALID_CATEGORIES,
        selected_category=category,
        selected_risk=risk_level,
        search_query=search_q
    )

@event_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "Other Outdoor Activity")
        event_date = request.form.get("event_date", "").strip()
        event_time = request.form.get("event_time", "10:00").strip()
        city = request.form.get("city", "").strip()
        venue_name = request.form.get("venue_name", "").strip()
        expected_participants = request.form.get("expected_participants", "50")
        description = request.form.get("description", "").strip()
        is_indoor = request.form.get("is_indoor") == "on"

        # Validation
        errors = []
        if not name:
            errors.append("Event name is required.")
        if not event_date:
            errors.append("Event date is required.")
        if not city:
            errors.append("Event city/location is required.")
        if not venue_name:
            errors.append("Venue name is required.")
        try:
            participants_int = int(expected_participants)
            if participants_int < 1:
                errors.append("Expected participants must be at least 1.")
        except ValueError:
            errors.append("Expected participants must be a valid number.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "events/create.html",
                categories=VALID_CATEGORIES,
                form_data=request.form
            )

        data = {
            "name": name,
            "category": category,
            "event_date": event_date,
            "event_time": event_time,
            "city": city,
            "venue_name": venue_name,
            "expected_participants": int(expected_participants),
            "description": description,
            "is_indoor": is_indoor
        }

        created = EventModel.create_event(session["user_id"], data)
        
        # Trigger immediate weather forecast & ML risk prediction
        try:
            RiskAnalyzer.analyze_event_risk(created["_id"], trigger_notifications=True)
        except Exception as e:
            flash(f"Event created, weather analysis noted: {e}", "info")

        flash(f"Event '{name}' created and weather risk analyzed successfully!", "success")
        return redirect(url_for("events.detail", event_id=str(created["_id"])))

    # Default date: tomorrow
    from datetime import timedelta
    default_date = (datetime.utcnow().date() + timedelta(days=1)).isoformat()
    return render_template(
        "events/create.html",
        categories=VALID_CATEGORIES,
        default_date=default_date
    )

@event_bp.route("/<event_id>")
@login_required
def detail(event_id):
    user_id = session["user_id"]
    event = EventModel.get_by_id(event_id, user_id=user_id)
    if not event:
        flash("Event not found or you do not have permission to view it.", "danger")
        return redirect(url_for("events.index"))

    # Fetch corresponding ML prediction document
    prediction = PredictionModel.get_by_event(event["_id"])

    return render_template(
        "events/detail.html",
        event=event,
        prediction=prediction
    )

@event_bp.route("/<event_id>/edit", methods=["GET", "POST"])
@login_required
def edit(event_id):
    user_id = session["user_id"]
    event = EventModel.get_by_id(event_id, user_id=user_id)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for("events.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", event.get("category"))
        event_date = request.form.get("event_date", "").strip()
        event_time = request.form.get("event_time", "10:00").strip()
        city = request.form.get("city", "").strip()
        venue_name = request.form.get("venue_name", "").strip()
        expected_participants = request.form.get("expected_participants", "50")
        description = request.form.get("description", "").strip()
        is_indoor = request.form.get("is_indoor") == "on"

        if not name or not event_date or not city or not venue_name:
            flash("All essential fields (Name, Date, City, Venue) are required.", "danger")
            return render_template("events/edit.html", event=event, categories=VALID_CATEGORIES)

        date_or_loc_changed = (event_date != event["event_date"] or city.lower() != event["city"].lower())

        update_data = {
            "name": name,
            "category": category,
            "event_date": event_date,
            "event_time": event_time,
            "city": city,
            "venue_name": venue_name,
            "expected_participants": int(expected_participants or 50),
            "description": description,
            "is_indoor": is_indoor
        }

        EventModel.update_event(event_id, user_id, update_data)

        if date_or_loc_changed:
            RiskAnalyzer.analyze_event_risk(event_id, trigger_notifications=True)

        flash("Event updated successfully!", "success")
        return redirect(url_for("events.detail", event_id=event_id))

    return render_template("events/edit.html", event=event, categories=VALID_CATEGORIES)

@event_bp.route("/<event_id>/delete", methods=["POST"])
@login_required
def delete(event_id):
    user_id = session["user_id"]
    success = EventModel.delete_event(event_id, user_id)
    if success:
        flash("Event deleted successfully.", "success")
    else:
        flash("Failed to delete event.", "danger")
    return redirect(url_for("events.index"))

@event_bp.route("/<event_id>/refresh-risk", methods=["POST"])
@login_required
def refresh_risk(event_id):
    user_id = session["user_id"]
    event = EventModel.get_by_id(event_id, user_id=user_id)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for("events.index"))

    risk_data = RiskAnalyzer.analyze_event_risk(event_id, trigger_notifications=True)
    flash(f"Weather risk refreshed: {risk_data.get('risk_level', 'Done')}", "info")
    return redirect(url_for("events.detail", event_id=event_id))

