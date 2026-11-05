from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bson import ObjectId
from app.routes.auth_routes import login_required
from app.models.event_model import EventModel
from app.models.venue_model import VenueModel
from app.services.recommendation_service import RecommendationService

recommendation_bp = Blueprint("recommendations", __name__, url_prefix="/recommendations")

@recommendation_bp.route("/alternative-dates")
@login_required
def alternative_dates():
    user_id = session["user_id"]
    events = EventModel.list_by_user(user_id)
    
    selected_event_id = request.args.get("event_id")
    selected_event = None
    alternatives = []
    error = None

    if selected_event_id:
        selected_event = EventModel.get_by_id(selected_event_id, user_id=user_id)
    elif events:
        # Default to first event with moderate/high risk or first event overall
        risky = [e for e in events if e.get("weather_risk", {}).get("risk_level") in ("High Risk", "Moderate Risk")]
        selected_event = risky[0] if risky else events[0]
        selected_event_id = str(selected_event["_id"])

    if selected_event:
        alternatives, err = RecommendationService.get_alternative_dates(selected_event["_id"], user_id=user_id)
        if err:
            error = err

    return render_template(
        "recommendations/alternative_dates.html",
        events=events,
        selected_event=selected_event,
        alternatives=alternatives,
        error=error
    )

@recommendation_bp.route("/alternative-dates/apply", methods=["POST"])
@login_required
def apply_date():
    user_id = session["user_id"]
    event_id = request.form.get("event_id")
    new_date = request.form.get("new_date")

    if not event_id or not new_date:
        flash("Event and target alternative date are required.", "danger")
        return redirect(url_for("recommendations.alternative_dates"))

    success, msg = RecommendationService.apply_alternative_date(event_id, user_id, new_date)
    if success:
        flash(f"Event successfully rescheduled to {new_date}! Weather risk has been re-evaluated.", "success")
        return redirect(url_for("events.detail", event_id=event_id))
    else:
        flash(f"Rescheduling error: {msg}", "danger")
        return redirect(url_for("recommendations.alternative_dates", event_id=event_id))

@recommendation_bp.route("/indoor-venues")
@login_required
def indoor_venues():
    user_id = session["user_id"]
    events = EventModel.list_by_user(user_id)
    
    selected_event_id = request.args.get("event_id")
    selected_event = None
    
    city_filter = request.args.get("city", "")
    type_filter = request.args.get("venue_type", "all")
    min_capacity = request.args.get("min_capacity", "0")

    if selected_event_id:
        selected_event = EventModel.get_by_id(selected_event_id, user_id=user_id)
        if selected_event and not city_filter:
            city_filter = selected_event["city"]
        if selected_event and min_capacity == "0":
            min_capacity = str(selected_event.get("expected_participants", 50))

    try:
        min_cap_int = int(min_capacity or 0)
    except ValueError:
        min_cap_int = 0

    venues = VenueModel.search_venues(
        city=city_filter if city_filter else None,
        min_capacity=min_cap_int,
        venue_type=type_filter if type_filter != "all" else None,
        only_available=False
    )

    return render_template(
        "recommendations/indoor_venues.html",
        events=events,
        selected_event=selected_event,
        venues=venues,
        city_filter=city_filter,
        type_filter=type_filter,
        min_capacity=min_capacity
    )

@recommendation_bp.route("/indoor-venues/apply", methods=["POST"])
@login_required
def apply_venue():
    user_id = session["user_id"]
    event_id = request.form.get("event_id")
    venue_id = request.form.get("venue_id")

    if not event_id or not venue_id:
        flash("Event and indoor venue selection are required.", "danger")
        return redirect(url_for("recommendations.indoor_venues"))

    success, msg = RecommendationService.apply_indoor_venue(event_id, user_id, venue_id)
    if success:
        flash("Event successfully moved to indoor venue! Weather risk eliminated.", "success")
        return redirect(url_for("events.detail", event_id=event_id))
    else:
        flash(f"Venue relocation error: {msg}", "danger")
        return redirect(url_for("recommendations.indoor_venues", event_id=event_id))

