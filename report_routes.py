from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, session
from bson import ObjectId
from app.routes.auth_routes import login_required
from app.models.event_model import EventModel
from app.models.prediction_model import PredictionModel
from app.models.venue_model import VenueModel
from app.services.pdf_service import PDFService
from app.services.recommendation_service import RecommendationService

report_bp = Blueprint("reports", __name__, url_prefix="/reports")

@report_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    events = EventModel.list_by_user(user_id)
    predictions = PredictionModel.list_by_user(user_id)
    pred_map = {str(p.get("event_id")): p for p in predictions}

    # Aggregate statistics
    total = len(events)
    safe_cnt = sum(1 for e in events if e.get("weather_risk", {}).get("risk_level") == "Low Risk")
    mod_cnt = sum(1 for e in events if e.get("weather_risk", {}).get("risk_level") == "Moderate Risk")
    high_cnt = sum(1 for e in events if e.get("weather_risk", {}).get("risk_level") == "High Risk")
    unverified_cnt = sum(1 for e in events if e.get("weather_risk", {}).get("risk_level") in ("Beyond Forecast Horizon", "Pending Analysis"))
    indoor_cnt = sum(1 for e in events if e.get("is_indoor"))
    rescheduled_cnt = sum(1 for e in events if e.get("reschedule_history"))

    stats = {
        "total": total,
        "safe": safe_cnt,
        "moderate": mod_cnt,
        "high": high_cnt,
        "unverified": unverified_cnt,
        "indoor": indoor_cnt,
        "rescheduled": rescheduled_cnt
    }

    return render_template(
        "reports/index.html",
        events=events,
        pred_map=pred_map,
        stats=stats
    )

@report_bp.route("/event/<event_id>/pdf")
@login_required
def download_event_pdf(event_id):
    user_id = session["user_id"]
    event = EventModel.get_by_id(event_id, user_id=user_id)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for("reports.index"))

    prediction = PredictionModel.get_by_event(event["_id"])
    
    # Get alternatives & indoor venues for report
    alternatives, _ = RecommendationService.get_alternative_dates(event["_id"], user_id=user_id)
    indoor_venues, _, _ = RecommendationService.get_indoor_venues(event["_id"])

    pdf_buffer = PDFService.generate_event_report(
        event=event,
        prediction=prediction,
        alternatives=alternatives[:3] if alternatives else [],
        indoor_venues=indoor_venues[:2] if indoor_venues else []
    )

    clean_name = "".join(c for c in event["name"] if c.isalnum() or c in (" ", "_", "-")).strip()
    filename = f"SkyPlan_Report_{clean_name}_{event['event_date']}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

