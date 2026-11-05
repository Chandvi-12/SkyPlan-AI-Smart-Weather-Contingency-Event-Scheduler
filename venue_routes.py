from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.routes.auth_routes import login_required
from app.models.venue_model import VenueModel

venue_bp = Blueprint("venues", __name__, url_prefix="/venues")

@venue_bp.route("/")
@login_required
def index():
    city = request.args.get("city", "").strip()
    venue_type = request.args.get("type", "all")
    min_capacity = request.args.get("min_capacity", "0")

    try:
        min_cap = int(min_capacity or 0)
    except ValueError:
        min_cap = 0

    venues = VenueModel.search_venues(
        city=city if city else None,
        min_capacity=min_cap,
        venue_type=venue_type if venue_type != "all" else None,
        only_available=False
    )

    return render_template(
        "recommendations/venue_directory.html",
        venues=venues,
        city=city,
        venue_type=venue_type,
        min_capacity=min_capacity
    )

@venue_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        address = request.form.get("address", "").strip()
        venue_type = request.form.get("venue_type", "Banquet Hall")
        capacity = request.form.get("capacity", "100")
        facilities = request.form.getlist("facilities")
        contact_phone = request.form.get("contact_phone", "").strip()
        contact_email = request.form.get("contact_email", "").strip()

        if not name or not city or not address:
            flash("Name, City, and Address are required.", "danger")
            return render_template("recommendations/venue_add.html")

        try:
            cap_int = int(capacity)
        except ValueError:
            cap_int = 100

        data = {
            "name": name,
            "city": city,
            "address": address,
            "venue_type": venue_type,
            "capacity": cap_int,
            "facilities": facilities if facilities else ["Air Conditioning", "Lighting", "Audio"],
            "availability_status": "Available",
            "contact_phone": contact_phone,
            "contact_email": contact_email
        }
        VenueModel.create_venue(data)
        flash(f"Indoor venue '{name}' added successfully!", "success")
        return redirect(url_for("venues.index"))

    return render_template("recommendations/venue_add.html")

