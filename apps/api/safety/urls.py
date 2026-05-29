from django.urls import path

from . import views

urlpatterns = [
    path("admin/safety/overview", views.overview, name="safety-overview"),
    path("admin/safety/risk-events", views.risk_events, name="safety-risk-events"),
    path(
        "admin/safety/risk-events/<int:pk>/resolve", views.resolve_risk, name="safety-risk-resolve"
    ),
    path("admin/safety/flags", views.content_flags, name="safety-flags"),
    path("admin/safety/flags/<int:pk>/resolve", views.resolve_flag, name="safety-flag-resolve"),
]
