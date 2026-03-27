import re
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for

from forms import PurchaseRequestForm
from models import Artwork, ArtworkView, PurchaseRequest, Visit

from . import public_bp


@public_bp.app_template_filter("slugify")
def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "artwork"


@public_bp.get("/media/artworks/<int:artwork_id>/<slug>.jpg")
def artwork_image(artwork_id: int, slug: str):
    artwork = Artwork.get_or_404(artwork_id)
    return redirect(artwork.image_filename, code=302)


@public_bp.get("/")
def home():
    featured = Artwork.random(limit=4)
    return render_template("index.html", featured=featured)


@public_bp.get("/artworks")
def artworks():
    all_artworks = Artwork.find(sort=[("created_at", -1)])
    return render_template("public/artworks.html", artworks=all_artworks)


@public_bp.get("/artworks/<int:artwork_id>")
def artwork_detail(artwork_id: int):
    artwork = Artwork.get_or_404(artwork_id)
    ArtworkView(artwork_id=artwork.id).save()
    return render_template("public/artwork_detail.html", artwork=artwork)


@public_bp.route("/artworks/<int:artwork_id>/request", methods=["GET", "POST"])
def request_artwork(artwork_id: int):
    artwork = Artwork.get_or_404(artwork_id)
    form = PurchaseRequestForm()

    if form.validate_on_submit():
        request_entry = PurchaseRequest(
            full_name=form.full_name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            message=form.message.data,
            artwork_id=artwork.id,
            artwork_title_snapshot=artwork.title,
            status="new",
        )
        request_entry.save()
        flash("Thank you. You will be contacted shortly with details.", "success")
        return redirect(url_for("public.request_success"))

    return render_template("public/request_artwork.html", artwork=artwork, form=form)


@public_bp.get("/request/success")
def request_success():
    return render_template("public/request_success.html")


@public_bp.before_request
def track_visits():
    if request.method != "GET":
        return
    # Count a visit when the homepage is opened
    if request.path == "/":
        Visit(
            path=request.path,
            ip=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=request.user_agent.string[:200],
        ).save()
