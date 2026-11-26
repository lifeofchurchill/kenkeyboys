"""
Settings for the Kenkey Boys website.

Anything secret, or anything that differs between your laptop and the
live server (the secret key, debug mode, the site's address), is read
from a file called .env next to manage.py. That file is never committed
to git, so the secrets never end up on GitHub.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# The project folder: the one that contains manage.py
BASE_DIR = Path(__file__).resolve().parent.parent

# Load the values from .env into the environment
load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    """Turn a comma-separated value like "a.com,b.com" into ["a.com", "b.com"]."""
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------- Security and environment ----------

# Signs logins and form tokens, so it must stay secret.
# If it's missing from .env, Django stops with an error instead of running unsafely.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Debug mode: on only when .env says exactly "True". If .env is missing,
# the site starts with debug OFF, which is the safe way to fail.
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

# Where "collectstatic" gathers every CSS, JS and image file for the live
# server, so its web server can hand them out quickly without Django
STATIC_ROOT = BASE_DIR / "staticfiles"


# ---------- Uploaded files (player photos, news images, club logos) ----------

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


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