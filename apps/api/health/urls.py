from django.urls import path

from .views import healthz, livez

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("livez", livez, name="livez"),
]
