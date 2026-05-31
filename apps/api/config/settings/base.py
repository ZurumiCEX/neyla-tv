"""Settings communs à tous les environnements (Phase 0 : minimum vital)."""

from __future__ import annotations

import ssl
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env()
environ.Env.read_env(BASE_DIR.parent.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-key")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "daphne",
    "config.apps.NeylaAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "channels",
    # Local
    "accounts",
    "analytics",
    "announcements",
    "audit",
    "catalog",
    "channels_app",
    "charity",
    "chat",
    "gamification",
    "health",
    "invitations",
    "moderation",
    "notifications",
    "ops",
    "payments",
    "safety",
    "social",
    "streamers",
    "subscriptions",
    "uploads",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sert les fichiers statiques (admin/DRF) sans nginx — requis
    # sur les PaaS type DigitalOcean App Platform. Doit suivre SecurityMiddleware.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Mode maintenance : bloque tout sauf staff + IPs allow-listées (cf. ops/middleware.py).
    "ops.middleware.MaintenanceModeMiddleware",
]

# IPs autorisées à bypasser le mode maintenance (admin techniques en intervention).
MAINTENANCE_ALLOWED_IPS = env.list("MAINTENANCE_ALLOWED_IPS", default=[])

# Cloudflare Turnstile (captcha gratuit, performant en Afrique). Vide → désactivé.
TURNSTILE_SITE_KEY = env("TURNSTILE_SITE_KEY", default="")
TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY", default="")

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="neyla"),
        "USER": env("POSTGRES_USER", default="neyla"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="neyla"),
        "HOST": env("POSTGRES_HOST", default="postgres"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        # Postgres managé (DO App Platform) impose TLS : POSTGRES_SSLMODE=require.
        # En local, "prefer" se rabat sur du non-TLS sans erreur.
        "OPTIONS": {"sslmode": env("POSTGRES_SSLMODE", default="prefer")},
    }
}

AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF / JWT ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "config.exception_handler.exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Neyla TV API",
    "DESCRIPTION": "API de la plateforme de streaming Neyla TV.",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Cookie pour stocker le refresh token côté navigateur (HttpOnly, SameSite=Lax).
REFRESH_COOKIE_NAME = "neyla_refresh"
REFRESH_COOKIE_MAX_AGE = int(SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
REFRESH_COOKIE_SECURE = not DEBUG
REFRESH_COOKIE_SAMESITE = "Lax"
REFRESH_COOKIE_PATH = "/api/auth/"

# --- Emails ---
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="no-reply@neyla.tv")
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# --- Web Push (VAPID) ---
# Si les clés ne sont pas configurées → push désactivé (dégradation propre).
VAPID_PUBLIC_KEY = env("VAPID_PUBLIC_KEY", default="")
VAPID_PRIVATE_KEY = env("VAPID_PRIVATE_KEY", default="")
VAPID_ADMIN_EMAIL = env("VAPID_ADMIN_EMAIL", default="admin@neyla.tv")

# --- CORS ---
CORS_ALLOWED_ORIGINS = env.list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000"],
)


# --- Redis / Channels ---
def _with_cert_reqs(url: str) -> str:
    """Redis managé (rediss://) utilise un certificat signé par une CA privée.

    redis-py et channels-redis lisent ``ssl_cert_reqs`` depuis la query string
    (valeurs : none/optional/required). On chiffre sans vérifier la chaîne CA,
    suffisant pour un trafic interne au datacenter (cf. ADR 008).
    """
    if url.startswith("rediss://") and "ssl_cert_reqs" not in url:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}ssl_cert_reqs=none"
    return url


REDIS_URL = _with_cert_reqs(env("REDIS_URL", default="redis://redis:6379/0"))

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

# --- Celery ---
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/2")
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TIMEZONE = TIME_ZONE
# Retry de connexion au broker au démarrage (broker managé/externe parfois lent).
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# Celery/kombu attendent la config TLS via un dict dédié (pas via la query URL).
if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
if CELERY_RESULT_BACKEND.startswith("rediss://"):
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}

# --- Streamers : quota quotidien d'approbations (gating, maîtrise des coûts) ---
STREAMER_DAILY_APPROVAL_QUOTA = env.int("STREAMER_DAILY_APPROVAL_QUOTA", default=100)

# --- Uploads médias (Cloudflare R2, S3-compatible) ---
# Si non configuré → mode FAKE (URL fake.local, pas d'appel réseau).
CLOUDFLARE_R2_ENDPOINT = env("CLOUDFLARE_R2_ENDPOINT", default="")
CLOUDFLARE_R2_BUCKET = env("CLOUDFLARE_R2_BUCKET", default="")
CLOUDFLARE_R2_ACCESS_KEY = env("CLOUDFLARE_R2_ACCESS_KEY", default="")
CLOUDFLARE_R2_SECRET_KEY = env("CLOUDFLARE_R2_SECRET_KEY", default="")
CLOUDFLARE_R2_PUBLIC_BASE_URL = env("CLOUDFLARE_R2_PUBLIC_BASE_URL", default="")

# --- Monétisation "Aura" ---
# Devise = FCFA (XOF). Prix d'1 Aura en XOF, part créateur (reste = commission).
AURA_UNIT_PRICE_XOF = env("AURA_UNIT_PRICE_XOF", default="5")
# Parité EUR FIXE (officielle) ; taux USD configurable manuellement (admin).
EUR_XOF_RATE = env("EUR_XOF_RATE", default="655.957")
USD_XOF_RATE = env("USD_XOF_RATE", default="600")
CREATOR_SHARE = env.float("CREATOR_SHARE", default=0.70)
# Commission plateforme prélevée sur un retrait (part créateur = 1 - ce taux).
WITHDRAWAL_FEE_PCT = env.float("WITHDRAWAL_FEE_PCT", default=0.30)
# fake (défaut, confirme tout de suite) | stripe | mobile_money | orange_money | wave
PAYMENTS_PROVIDER = env("PAYMENTS_PROVIDER", default="fake")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
# Mobile money (agrégateurs régionaux). Vides → repli FAKE (confirme en dev).
ORANGE_MONEY_API_KEY = env("ORANGE_MONEY_API_KEY", default="")
WAVE_API_KEY = env("WAVE_API_KEY", default="")

# --- Sécurité contenu (anti-violation) ---
# Fournisseur de vision pour l'analyse d'images (vide → heuristique texte seule).
SAFETY_VISION_PROVIDER = env("SAFETY_VISION_PROVIDER", default="")
# Mettre les images en file d'examen manuel quand aucun fournisseur de vision.
SAFETY_REVIEW_UPLOADS = env.bool("SAFETY_REVIEW_UPLOADS", default=False)

# --- Cloudflare Stream ---
# Si CLOUDFLARE_API_TOKEN est vide, on bascule sur un client FAKE en dev/tests
# qui retourne des URLs rtmps://fake.local pour développer hors-ligne.
CLOUDFLARE_ACCOUNT_ID = env("CLOUDFLARE_ACCOUNT_ID", default="")
CLOUDFLARE_API_TOKEN = env("CLOUDFLARE_API_TOKEN", default="")
CLOUDFLARE_WEBHOOK_SECRET = env("CLOUDFLARE_WEBHOOK_SECRET", default="dev-webhook-secret")
# Tolérance de fraîcheur de la signature webhook (anti-rejeu).
WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 5 * 60

# --- Logs JSON simples ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
