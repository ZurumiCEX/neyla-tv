"""URLs racine : admin + endpoints API montés sous /api/."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/schema",
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name="schema",
    ),
    path(
        "api/docs",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="swagger-ui",
    ),
    path("api/", include("health.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("channels_app.urls")),
    path("api/", include("chat.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("social.urls")),
    path("api/", include("streamers.urls")),
    path("api/", include("notifications.urls")),
    path("api/", include("moderation.urls")),
    path("api/", include("analytics.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("uploads.urls")),
]
