from app.routes.auth_routes import auth_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.event_routes import event_bp
from app.routes.weather_routes import weather_bp
from app.routes.prediction_routes import prediction_bp
from app.routes.recommendation_routes import recommendation_bp
from app.routes.notification_routes import notification_bp
from app.routes.report_routes import report_bp
from app.routes.venue_routes import venue_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "event_bp",
    "weather_bp",
    "prediction_bp",
    "recommendation_bp",
    "notification_bp",
    "report_bp",
    "venue_bp"
]

