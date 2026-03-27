from flask import Blueprint, flash, redirect, render_template, request, url_for


index_bp = Blueprint("index_bp", __name__)

# Temporary in-memory storage for orders (replace with a database later).
ORDERS = []


@index_bp.get("/")
def home():
    return render_template("index.html")


@index_bp.post("/order")
def order():
    name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()
    delivery_location = request.form.get("delivery_location", "").strip()

    if not name or not phone or not message or not delivery_location:
        flash("Please fill in the required fields: name, phone, message, and delivery location.", "error")
        return redirect(url_for("index_bp.home") + "#contact")

    order_data = {
        "name": name,
        "phone": phone,
        "email": request.form.get("email", "").strip(),
        "artwork_type": request.form.get("artwork_type", "").strip(),
        "size": request.form.get("size", "").strip(),
        "reference_url": request.form.get("reference_url", "").strip(),
        "message": message,
        "delivery_location": delivery_location,
    }

    ORDERS.append(order_data)
    flash("Thanks! Your order request was received. We will contact you shortly.", "success")
    return redirect(url_for("index_bp.home") + "#contact")
