from flask import Blueprint, render_template, request, jsonify, session
from bson import ObjectId
from app.routes.auth_routes import login_required
from app.models.prediction_model import PredictionModel
from app.models.event_model import EventModel
from app.services.ml_service import get_ml_service, calculate_heat_index

prediction_bp = Blueprint("predictions", __name__, url_prefix="/predictions")

@prediction_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    ml = get_ml_service()
    
    # User's predictions
    predictions = PredictionModel.list_by_user(user_id)
    events = EventModel.list_by_user(user_id)
    event_map = {str(e["_id"]): e for e in events}
    
    # Merge event names
    for p in predictions:
        eid = str(p.get("event_id"))
        p["event_name"] = event_map.get(eid, {}).get("name", "Event")
        p["category"] = event_map.get(eid, {}).get("category", "General")

    metadata = ml.get_metadata()

    return render_template(
        "predictions/index.html",
        predictions=predictions,
        metadata=metadata
    )

@prediction_bp.route("/simulator", methods=["GET", "POST"])
@login_required
def simulator():
    ml = get_ml_service()
    result = None
    inputs = {
        "temperature": 32.0,
        "humidity": 75.0,
        "rain_probability": 65.0,
        "rainfall_mm": 6.5,
        "wind_speed": 22.0
    }

    if request.method == "POST":
        try:
            inputs["temperature"] = float(request.form.get("temperature", 32.0))
            inputs["humidity"] = float(request.form.get("humidity", 75.0))
            inputs["rain_probability"] = float(request.form.get("rain_probability", 65.0))
            inputs["rainfall_mm"] = float(request.form.get("rainfall_mm", 6.5))
            inputs["wind_speed"] = float(request.form.get("wind_speed", 22.0))
            
            rainout = ml.predict_rainout(
                temperature=inputs["temperature"],
                humidity=inputs["humidity"],
                rain_probability=inputs["rain_probability"],
                rainfall_mm=inputs["rainfall_mm"],
                wind_speed=inputs["wind_speed"]
            )
            
            heat_idx = calculate_heat_index(inputs["temperature"], inputs["humidity"])
            heat = ml.predict_heat(
                temperature=inputs["temperature"],
                humidity=inputs["humidity"],
                wind_speed=inputs["wind_speed"],
                heat_index=heat_idx
            )
            
            result = {
                "rainout": rainout,
                "heat": heat,
                "heat_index": heat_idx
            }
        except Exception as e:
            result = {"error": str(e)}

    return render_template("predictions/simulator.html", inputs=inputs, result=result)

@prediction_bp.route("/api/simulate", methods=["POST"])
@login_required
def api_simulate():
    ml = get_ml_service()
    data = request.get_json() or {}
    try:
        temp = float(data.get("temperature", 28.0))
        hum = float(data.get("humidity", 60.0))
        prob = float(data.get("rain_probability", 20.0))
        rain = float(data.get("rainfall_mm", 0.0))
        wind = float(data.get("wind_speed", 12.0))

        rainout = ml.predict_rainout(temp, hum, prob, rain, wind)
        heat_idx = calculate_heat_index(temp, hum)
        heat = ml.predict_heat(temp, hum, wind, heat_idx)

        return jsonify({
            "success": True,
            "rainout": rainout,
            "heat": heat,
            "heat_index": heat_idx
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

