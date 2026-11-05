from flask import Blueprint, render_template, request, jsonify, session
from app.routes.auth_routes import login_required
from app.services.weather_service import WeatherService
from app.models.event_model import EventModel

weather_bp = Blueprint("weather", __name__, url_prefix="/weather")

@weather_bp.route("/")
@login_required
def forecast_view():
    user_id = session.get("user_id")
    # Default city from user's first event or 'Delhi'
    default_city = "Delhi"
    user_events = EventModel.list_by_user(user_id)
    if user_events and user_events[0].get("city"):
        default_city = user_events[0]["city"]

    city = request.args.get("city", default_city).strip()
    if not city:
        city = default_city

    forecast_days, loc = WeatherService.get_14day_forecast(city)

    return render_template(
        "weather/forecast.html",
        city=city,
        location=loc,
        forecast_days=forecast_days
    )

@weather_bp.route("/api/predict")
@login_required
def api_predict():
    """Return ML predictions (rainout & heat) for the next 14‑day forecast.
    Also includes model metadata (accuracy, precision, recall) so the caller can verify
    that the models perform > 90 % on the training/validation set.
    """
    city = request.args.get("city", "Delhi").strip()
    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    # Get the 14‑day forecast (real or synthetic) from the weather service
    forecast_days, loc = WeatherService.get_14day_forecast(city)

    # Run both ML models on each day of the forecast
    from app.services.ml_service import get_ml_service
    ml_service = get_ml_service()
    predictions = []
    for day in forecast_days:
        day_pred = ml_service.predict_both_for_forecast(day)
        # Attach the date for reference
        day_pred["date"] = day.get("date")
        predictions.append(day_pred)

    # Pull model metadata (accuracy etc.) to expose to the client
    metadata = ml_service.get_metadata()

    return jsonify({
        "city": city,
        "location": loc,
        "predictions": predictions,
        "model_metadata": metadata
    })

@weather_bp.route("/api/forecast")
@login_required
def api_forecast():
    city = request.args.get("city", "Delhi").strip()
    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    forecast_days, loc = WeatherService.get_14day_forecast(city)
    return jsonify({
        "city": city,
        "location": loc,
        "forecast": forecast_days
    })
