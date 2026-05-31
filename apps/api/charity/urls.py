from django.urls import path

from . import views

urlpatterns = [
    path("charity/events", views.list_events, name="charity-events"),
    path("charity/events/current", views.current_event, name="charity-current"),
    path("charity/events/<slug:slug>", views.event_detail, name="charity-event-detail"),
    path("charity/charities", views.list_charities, name="charity-list"),
    path("charity/donate", views.donate, name="charity-donate"),
]

# Calendrier d'événements de plateforme.
urlpatterns += [
    path("events", views.list_platform_events, name="platform-events"),
    path("events/upcoming", views.list_upcoming_platform_events, name="platform-events-upcoming"),
    path("events/<slug:slug>", views.platform_event_detail, name="platform-event-detail"),
]
