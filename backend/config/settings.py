from pathlib import Path

from config.env import env, load_env

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

load_env()

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Base URL of the Vue app, used to build invitation links.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:8000")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_vite",
    "apps.accounts",
    "apps.invaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite by default (a file next to manage.py); DATABASE_URL can point elsewhere, e.g. PostgreSQL.
DATABASES = {
    "default": env.db_url_config(env("DATABASE_URL", default="") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"]["OPTIONS"] = {
        # WAL lets readers work while a write is in progress; writers wait instead of failing
        # with "database is locked" when several Gunicorn workers write at once.
        "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA foreign_keys=ON;",
        "transaction_mode": "IMMEDIATE",
        "timeout": 20,
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# The UI is French only: Django and DRF messages are returned in French.
LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", "Français")]
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# The Vue app, built by Vite into frontend/dist (served under /static/).
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
# Built files first; frontend/public also serves favicon and icons before any build.
STATICFILES_DIRS = [path for path in (FRONTEND_DIST_DIR, FRONTEND_DIR / "public") if path.exists()]

# Dev mode: scripts come from the Vite dev server (hot reload, `npm run dev`).
# Otherwise: hashed files from the Vite build manifest (`npm run build`).
DJANGO_VITE = {
    "default": {
        "dev_mode": env.bool("DJANGO_VITE_DEV_MODE", default=DEBUG),
        "dev_server_host": env("DJANGO_VITE_DEV_SERVER_HOST", default="localhost"),
        "dev_server_port": env.int("DJANGO_VITE_DEV_SERVER_PORT", default=5173),
        "manifest_path": FRONTEND_DIST_DIR / ".vite" / "manifest.json",
    }
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_FAILURE_VIEW = "config.exceptions.csrf_failure"
# Browsers' default policy: other sites only get our origin, never the page path. OSM tile
# servers block requests without a Referer, which Django's default ("same-origin") removes.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.accounts.permissions.IsTeamMember",
    ],
    "EXCEPTION_HANDLER": "config.exceptions.exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "geocode": "30/min",
    },
}

INVITATION_VALIDITY_DAYS = 7

# Sent to Nominatim for reverse geocoding; its usage policy requires an identifying value.
GEOCODER_USER_AGENT = env("GEOCODER_USER_AGENT", default="Invaders/1.0 (team map for Space Invaders)")

# Map tiles are relayed from OpenStreetMap (apps/invaders/tiles.py) and cached on disk.
TILE_USER_AGENT = env("TILE_USER_AGENT", default=GEOCODER_USER_AGENT)
TILE_CACHE_DIR = Path(env("TILE_CACHE_DIR", default=str(BASE_DIR / "tile_cache")))
# Cached tiles not refreshed for this many days are deleted automatically (once a day).
TILE_CACHE_MAX_DAYS = env.int("TILE_CACHE_MAX_DAYS", default=7)
