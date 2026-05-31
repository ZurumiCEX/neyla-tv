from django.urls import path

from .views import healthz, livez, status_overview

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("livez", livez, name="livez"),
    path("status", status_overview, name="status"),
]
