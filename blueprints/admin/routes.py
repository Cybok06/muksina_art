import os
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash
import requests

from extensions import csrf
from forms import ArtworkEditForm, ArtworkForm, DeleteForm, LoginForm, RequestStatusForm
from models import Admin, Artwork, ArtworkView, PurchaseRequest, Visit

from . import admin_bp


@admin_bp.app_context_processor
def inject_request_counts():
    try:
        pending_count = PurchaseRequest.count({"status": "new"})
    except Exception:
        pending_count = 0
    return {"pending_request_count": pending_count}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


# Cloudflare Images (hardcoded as requested)
CF_ACCOUNT_ID = "63e6f91eec9591f77699c4b434ab44c6"
CF_IMAGES_TOKEN = "Brz0BEfl_GqEUjEghS2UEmLZhK39EUmMbZgu_hIo"
CF_HASH = "h9fmMoa1o2c2P55TcWJGOg"
DEFAULT_VARIANT = "public"

def _normalize_hashtags(raw: str) -> str:
    if not raw:
        return ""
    parts = []
    for chunk in raw.replace("#", " ").split(","):
        tag = chunk.strip()
        if not tag:
            continue
        parts.append(tag)
    # dedupe while preserving order
    seen = set()
    cleaned = []
    for tag in parts:
        lower = tag.lower()
        if lower in seen:
            continue
        seen.add(lower)
        cleaned.append(tag)
    return ", ".join(cleaned)

def _cloudflare_direct_upload():
    direct_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/images/v2/direct_upload"
    headers = {"Authorization": f"Bearer {CF_IMAGES_TOKEN}"}
    res = requests.post(direct_url, headers=headers, data={}, timeout=20)
    res.raise_for_status()
    data = res.json()
    if not data.get("success"):
        raise RuntimeError("Cloudflare direct upload failed")
    return data["result"]["uploadURL"], data["result"]["id"]


@admin_bp.post("/admin/cloudflare/direct-upload")
@admin_required
@csrf.exempt
def cloudflare_direct_upload():
    try:
        upload_url, image_id = _cloudflare_direct_upload()
        image_url = f"https://imagedelivery.net/{CF_HASH}/{image_id}/{DEFAULT_VARIANT}"
        return {"success": True, "upload_url": upload_url, "image_id": image_id, "image_url": image_url}
    except Exception as exc:
        return {"success": False, "error": str(exc)}, 500


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.find_one({"username": form.username.data})
        if not admin or not check_password_hash(admin.password_hash, form.password.data):
            flash("Invalid username or password.", "error")
            return render_template("admin/login.html", form=form)

        session["admin_id"] = admin.id
        flash("Welcome back.", "success")
        next_url = request.args.get("next") or url_for("admin.dashboard")
        return redirect(next_url)

    return render_template("admin/login.html", form=form)


@admin_bp.get("/admin/logout")
def logout():
    session.pop("admin_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.get("/admin")
@admin_required
def dashboard():
    artwork_count = Artwork.count()
    request_count = PurchaseRequest.count()
    total_visits = Visit.count()
    total_artwork_views = ArtworkView.count()

    since = datetime.utcnow() - timedelta(days=6)
    trend_rows = Visit.aggregate(
        [
            {"$match": {"created_at": {"$gte": since}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
    )
    trend_map = {row["_id"]: row["count"] for row in trend_rows}
    trend = []
    for i in range(7):
        day = (since + timedelta(days=i)).date()
        trend.append({"date": day.strftime("%Y-%m-%d"), "count": trend_map.get(str(day), 0)})

    top_rows = ArtworkView.aggregate(
        [
            {"$group": {"_id": "$artwork_id", "views": {"$sum": 1}}},
            {"$sort": {"views": -1}},
            {"$limit": 5},
        ]
    )
    top_ids = [row["_id"] for row in top_rows]
    artworks = {art.id: art for art in Artwork.find_by_ids(top_ids)}
    top_artworks = [(artworks.get(row["_id"]), row["views"]) for row in top_rows if artworks.get(row["_id"])]

    recent_requests = PurchaseRequest.find(sort=[("created_at", -1)], limit=5)
    return render_template(
        "admin/dashboard.html",
        artwork_count=artwork_count,
        request_count=request_count,
        total_visits=total_visits,
        total_artwork_views=total_artwork_views,
        trend=trend,
        top_artworks=top_artworks,
        recent_requests=recent_requests,
    )


@admin_bp.route("/admin/artworks/new", methods=["GET", "POST"])
@admin_required
def upload_artwork():
    form = ArtworkForm()
    if form.validate_on_submit():
        filename = form.image_url.data
        if not filename:
            flash("Please upload an image first.", "error")
            return render_template("admin/artwork_form.html", form=form, mode="create")
        artwork = Artwork(
            title=form.title.data,
            description=form.description.data,
            image_filename=filename,
            hashtags=_normalize_hashtags(form.hashtags.data),
            status=form.status.data,
        )
        artwork.save()
        flash("Artwork uploaded successfully.", "success")
        return redirect(url_for("admin.manage_artworks"))

    return render_template("admin/artwork_form.html", form=form, mode="create")


@admin_bp.get("/admin/artworks")
@admin_required
def manage_artworks():
    artworks = Artwork.find(sort=[("created_at", -1)])
    return render_template("admin/manage_artworks.html", artworks=artworks)


@admin_bp.route("/admin/artworks/<int:artwork_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_artwork(artwork_id: int):
    artwork = Artwork.get_or_404(artwork_id)
    form = ArtworkEditForm(obj=artwork)

    if form.validate_on_submit():
        artwork.title = form.title.data
        artwork.description = form.description.data
        artwork.hashtags = _normalize_hashtags(form.hashtags.data)
        artwork.status = form.status.data

        if form.image_url.data:
            artwork.image_filename = form.image_url.data

        artwork.save()
        flash("Artwork updated.", "success")
        return redirect(url_for("admin.manage_artworks"))

    if request.method == "GET":
        form.hashtags.data = artwork.hashtags
    return render_template("admin/artwork_form.html", form=form, mode="edit", artwork=artwork)


@admin_bp.route("/admin/artworks/<int:artwork_id>/delete", methods=["GET", "POST"])
@admin_required
def delete_artwork(artwork_id: int):
    artwork = Artwork.get_or_404(artwork_id)
    form = DeleteForm()
    if request.method == "POST":
        if form.validate_on_submit():
            artwork.delete()
            flash("Artwork deleted.", "success")
            return redirect(url_for("admin.manage_artworks"))
        flash("Invalid delete request.", "error")
    return render_template("admin/confirm_delete.html", artwork=artwork, form=form)


@admin_bp.route("/admin/requests", methods=["GET", "POST"])
@admin_required
def view_requests():
    requests = PurchaseRequest.find(sort=[("created_at", -1)])

    if request.method == "POST":
        request_id = request.form.get("request_id")
        try:
            request_id_int = int(request_id)
        except Exception:
            request_id_int = None
        req = PurchaseRequest.get_or_404(request_id_int)
        form = RequestStatusForm(prefix=request_id)
        if form.validate_on_submit():
            req.status = form.status.data
            req.save()
            flash("Request status updated.", "success")
            return redirect(url_for("admin.view_requests"))
        flash("Invalid status update.", "error")

    request_forms = []
    for req in requests:
        form = RequestStatusForm(prefix=str(req.id))
        form.status.data = req.status
        request_forms.append((req, form))

    return render_template("admin/requests.html", request_forms=request_forms)
