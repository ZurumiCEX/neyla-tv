from django.urls import path

from . import views

urlpatterns = [
    path("notifications", views.list_notifications, name="notifications-list"),
    path("notifications/read", views.mark_read, name="notifications-read"),
]
