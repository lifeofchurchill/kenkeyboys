"""
Settings for the Kenkey Boys website.

Anything secret, or anything that differs between your laptop and the
live server (the secret key, debug mode, the site's address, the database,
the photo storage), is read from a file called .env next to manage.py,
or from the host's environment variables. That file is never committed to git.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# The project folder: the one that contains manage.py
BASE_DIR = Path(__file__).resolve().parent.parent

# Load the values from .env into the environment (if the file exists)
load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    """Turn a comma-separated value like "a.com,b.com" into ["a.com", "b.com"]."""
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------- Security and environment ----------

# Signs logins and form tokens, so it must stay secret.
# If it's missing, Django stops with an error instead of running unsafely.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Debug mode: on only when the environment says exactly "True".
# If it's missing, the site starts with debug OFF, which is the safe way to fail.
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

# The web addresses this site answers to
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")

# Full https:// addresses allowed to send forms (the Join form and the admin login)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# On the live site, only send login and form cookies over HTTPS
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# ---------- Apps ----------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    # Our apps
    "accounts",
    "club",
    "matches",
    "website",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,  # finds templates inside each app's "templates" folder
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


# ---------- Database ----------

if os.environ.get("DATABASE_URL"):
    # Postgres on Neon. dj_database_url turns the connection string into Django settings.
    # conn_max_age=0: open a fresh connection per request; Neon's pooler shares them out
    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=0)}
    # The pooler hands each query to whichever connection is free, which breaks
    # Postgres "server-side cursors" (used for very big result sets), so turn them off
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    # No DATABASE_URL: use the local SQLite file (a practice copy on the laptop)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------- Users and passwords ----------

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------- Language and time ----------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Accra"  # Ghana time: the same as UTC all year round
USE_I18N = True
USE_TZ = True


# ---------- Static files (CSS, JavaScript, the crest) ----------

STATIC_URL = "static/"

# Where "collectstatic" gathers every CSS, JS and image file.
# Vercel runs collectstatic itself and serves this folder from its CDN
STATIC_ROOT = BASE_DIR / "staticfiles"


# ---------- Uploaded files (player photos, news images, club logos) ----------

# Used when no bucket is set up: files go in the local media folder
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

if os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    # Hosts built on Amazon's servers (like Vercel) can put their own temporary
    # AWS "session token" into the environment. Neon's keys don't use one, and
    # mixing it in would make Neon reject every upload, so remove it first
    os.environ.pop("AWS_SESSION_TOKEN", None)
    os.environ.pop("AWS_SECURITY_TOKEN", None)

    # Uploads go to the Neon bucket instead, because Vercel can't keep files on its own disk
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        # CSS/JS stay normal static files, which Vercel serves itself
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
    AWS_S3_ENDPOINT_URL = os.environ["AWS_ENDPOINT_URL_S3"]
    AWS_S3_REGION_NAME = os.environ.get("AWS_REGION", "us-east-2")
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    # Neon only understands addresses like endpoint/bucket/file, not bucket.endpoint/file
    AWS_S3_ADDRESSING_STYLE = "path"
    # Don't send per-file permissions: Neon doesn't support them. The bucket itself is public
    AWS_DEFAULT_ACL = None
    # Plain public links, instead of long links that expire after an hour
    AWS_QUERYSTRING_AUTH = False
    # Two uploads both called photo.jpg get different names instead of replacing each other
    AWS_S3_FILE_OVERWRITE = False
    # Only add upload checksums when required; some S3-style services reject the newer default
    os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
    os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------- API ----------

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"trials": "5/hour"},  # trial requests per visitor
}


# ---------- EA Pro Clubs ----------

EA_CLUB_ID = "78431"
EA_PLATFORM = "common-gen5"
EA_SEASON = "FC 27"


# ---------- EA sync (not used once the database is on Neon) ----------

EA_SYNC_TOKEN = os.environ.get("EA_SYNC_TOKEN", "")
EA_SYNC_URL = os.environ.get("EA_SYNC_URL", "")