from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from bson import ObjectId
from app.routes.auth_routes import login_required
from app.models.notification_model import NotificationModel

notification_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@notification_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    filter_type = request.args.get("type", "all")
    unread_only = (request.args.get("unread") == "true")
    
    notifications = NotificationModel.get_user_notifications(user_id, limit=50, unread_only=unread_only)
    
    if filter_type != "all":
        notifications = [n for n in notifications if n.get("type") == filter_type]
        
    unread_count = NotificationModel.get_unread_count(user_id)

    return render_template(
        "notifications/index.html",
        notifications=notifications,
        unread_count=unread_count,
        filter_type=filter_type,
        unread_only=unread_only
    )

@notification_bp.route("/<notif_id>/read", methods=["POST"])
@login_required
def mark_read(notif_id):
    user_id = session["user_id"]
    NotificationModel.mark_as_read(notif_id, user_id)
    return redirect(request.referrer or url_for("notifications.index"))

@notification_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    user_id = session["user_id"]
    NotificationModel.mark_all_as_read(user_id)
    flash("All notifications marked as read.", "success")
    return redirect(request.referrer or url_for("notifications.index"))

@notification_bp.route("/<notif_id>/delete", methods=["POST"])
@login_required
def delete(notif_id):
    user_id = session["user_id"]
    NotificationModel.delete_notification(notif_id, user_id)
    flash("Notification removed.", "info")
    return redirect(url_for("notifications.index"))

@notification_bp.route("/api/unread-count")
@login_required
def api_unread_count():
    user_id = session["user_id"]
    count = NotificationModel.get_unread_count(user_id)
    return jsonify({"unread_count": count})

