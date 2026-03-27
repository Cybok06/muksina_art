import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Core
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    BASE_URL = os.getenv("BASE_URL", "https://www.muksicreations.com")

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "artworks")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4MB
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # Dev admin seed (only used when no admin exists)
    # Hardcoded dev admin credentials (can still be overridden via env vars)
    DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "muksina")
    DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "muksina@12345")
