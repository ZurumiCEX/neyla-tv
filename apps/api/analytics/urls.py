from django.urls import path

from . import views

urlpatterns = [
    path("analytics/me", views.my_analytics, name="analytics-me"),
    path("analytics/me/revenue", views.my_revenue, name="analytics-me-revenue"),
    path("analytics/overview", views.overview, name="analytics-overview"),
    path("admin/dashboard", views.dashboard, name="admin-dashboard"),
    path("admin/monitoring", views.monitoring, name="admin-monitoring"),
]
