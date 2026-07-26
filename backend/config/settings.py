from datetime import timedelta
from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SECURITY: Secret Key & Debug
# ---------------------------------------------------------------------------
# SECURITY WARNING: No default fallback for SECRET_KEY in production.
# Must be set via .env file.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY and os.getenv("DJANGO_DEBUG", "False").lower() not in {"1", "true", "yes", "on"}:
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production environment.")
if not SECRET_KEY:
    SECRET_KEY = "dev-secret-key-insecure-do-not-use-in-production"

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if os.getenv("DJANGO_ALLOWED_HOSTS") else ["localhost", "127.0.0.1"] if DEBUG else []
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ---------------------------------------------------------------------------
# Installed Apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "accounts",
    "hospitals",
    "patients",
    "medrecords",
    "appointments",
    "lab",
    "files",
    "notifications",
    "audit",
    "stats",
    "reports",
]

AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "audit.middleware.AuditMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB_NAME = os.getenv("POSTGRES_DB", "hospital_cms")
POSTGRES_USER = os.getenv("POSTGRES_USER", "hospital")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "hospital_pass")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB_NAME,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST or "localhost",
        "PORT": POSTGRES_PORT,
    }
}

# Fallback to SQLite for local development without PostgreSQL
if os.getenv("USE_SQLITE", "").lower() in {"1", "true", "yes", "on"}:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz-UZ"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", BASE_DIR / "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/min",
        "login_burst": "10/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Hospital Central Management System API",
    "DESCRIPTION": "API documentation for HCMS",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------------------
# JWT (SimpleJWT) with Token Blacklist
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "BLACKLIST_AFTER_ROTATION": True,
}

# ---------------------------------------------------------------------------
# CORS – production-safe
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "").lower() in {"1", "true", "yes", "on"}
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", FRONTEND_URL).split(",")
    if origin.strip()
]
if not CORS_ALLOWED_ORIGINS and not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# ---------------------------------------------------------------------------
# HTTPS / Security Headers
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "").lower() in {"1", "true", "yes", "on"}

HSTS_SECONDS = int(os.getenv("HSTS_SECONDS", "0"))
if SECURE_SSL_REDIRECT and HSTS_SECONDS > 0:
    SECURE_HSTS_SECONDS = HSTS_SECONDS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes", "on"} if not DEBUG else False
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "").lower() in {"1", "true", "yes", "on"} if not DEBUG else False

# Referrer Policy
SECURE_REFERRER_POLICY = os.getenv("SECURE_REFERRER_POLICY", "same-origin")

# X-Frame-Options
X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")

# X-Content-Type-Options
SECURE_CONTENT_TYPE_NOSNIFF = True

# ---------------------------------------------------------------------------
# Content Security Policy
# ---------------------------------------------------------------------------
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required by Bootstrap JS
    "https://cdn.jsdelivr.net",  # Bootstrap/Chart.js CDN
    "https://unpkg.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required by Bootstrap
    "https://cdn.jsdelivr.net",
    "https://fonts.googleapis.com",
)
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
    "https://cdn.jsdelivr.net",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
)
CSP_CONNECT_SRC = (
    "'self'",
    "https://fonts.googleapis.com",
)
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

if DEBUG:
    CSP_SCRIPT_SRC += ("'unsafe-eval'",)

# ---------------------------------------------------------------------------
# Email Configuration
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in {"1", "true", "yes", "on"}
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@hospitalcms.com")

# ---------------------------------------------------------------------------
# Cache (required for throttling and lockout)
# ---------------------------------------------------------------------------
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "")
if CACHE_BACKEND:
    CACHES = {
        "default": {
            "BACKEND": CACHE_BACKEND,
            "LOCATION": os.getenv("CACHE_LOCATION", ""),
        }
    }
elif os.getenv("USE_SQLITE", "").lower() in {"1", "true", "yes", "on"} or "test" in sys.argv:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "hospital-cms-cache",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/0"),
        }
    }

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO" if not DEBUG else "DEBUG",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}