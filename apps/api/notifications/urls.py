from django.urls import path

from . import views

urlpatterns = [
    path("notifications", views.list_notifications, name="notifications-list"),
    path("notifications/read", views.mark_read, name="notifications-read"),
    path("notifications/preferences", views.preferences, name="notifications-preferences"),
    path("notifications/push/key", views.push_key, name="notifications-push-key"),
    path("notifications/push/subscribe", views.push_subscribe, name="notifications-push-subscribe"),
    path(
        "notifications/push/unsubscribe",
        views.push_unsubscribe,
        name="notifications-push-unsubscribe",
    ),
    path("notifications/<int:pk>/read", views.mark_one_read, name="notifications-read-one"),
    path("admin/messages", views.support_message, name="admin-support-message"),
]
