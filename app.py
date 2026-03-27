import os
import re
from xml.sax.saxutils import escape

from flask import Flask, Response, render_template, send_from_directory, url_for
from werkzeug.security import generate_password_hash

from blueprints.admin import admin_bp
from blueprints.public import public_bp
from config import Config
from extensions import csrf
from models import Admin, Artwork


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    favicon_dir = os.path.join(app.root_path, "static", "images")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(favicon_dir, "favicon.ico")

    @app.route("/favicon-96x96.png")
    def favicon_png():
        return send_from_directory(favicon_dir, "favicon-96x96.png")

    @app.route("/favicon.svg")
    def favicon_svg():
        return send_from_directory(favicon_dir, "favicon.svg")

    @app.route("/apple-touch-icon.png")
    def apple_touch_icon():
        return send_from_directory(favicon_dir, "apple-touch-icon.png")

    @app.route("/site.webmanifest")
    def site_manifest():
        return send_from_directory(favicon_dir, "site.webmanifest")

    @app.route("/web-app-manifest-192x192.png")
    def manifest_icon_192():
        return send_from_directory(favicon_dir, "web-app-manifest-192x192.png")

    @app.route("/web-app-manifest-512x512.png")
    def manifest_icon_512():
        return send_from_directory(favicon_dir, "web-app-manifest-512x512.png")

    @app.route("/robots.txt")
    def robots():
        return send_from_directory(app.root_path, "robots.txt")

    @app.route("/sitemap.xml")
    def sitemap():
        base = app.config.get("BASE_URL", "https://www.muksicreations.com").rstrip("/")

        def slugify(value: str) -> str:
            value = (value or "").strip().lower()
            value = re.sub(r"[^a-z0-9]+", "-", value)
            return value.strip("-") or "artwork"

        urls = []
        urls.append(
            {
                "loc": f"{base}/",
                "images": [f"{base}/static/images/profile_pic.jpeg"],
            }
        )
        urls.append({"loc": f"{base}/artworks", "images": []})

        artworks = Artwork.find(sort=[("created_at", -1)])
        for art in artworks:
            image_path = url_for("public.artwork_image", artwork_id=art.id, slug=slugify(art.title))
            urls.append(
                {
                    "loc": f"{base}/artworks/{art.id}",
                    "images": [f"{base}{image_path}"],
                }
            )

        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
        ]
        for entry in urls:
            xml.append("  <url>")
            xml.append(f"    <loc>{escape(entry['loc'])}</loc>")
            for img in entry["images"]:
                xml.append("    <image:image>")
                xml.append(f"      <image:loc>{escape(img)}</image:loc>")
                xml.append("    </image:image>")
            xml.append("  </url>")
        xml.append("</urlset>")
        return Response("\n".join(xml), mimetype="application/xml")

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    with app.app_context():
        if not Admin.find_one():
            admin = Admin(
                username=app.config["DEFAULT_ADMIN_USERNAME"],
                password_hash=generate_password_hash(app.config["DEFAULT_ADMIN_PASSWORD"]),
            )
            admin.save()

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1"
    app.run(debug=debug_mode)
