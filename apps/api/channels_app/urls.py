from django.urls import path

from . import views, webhooks

urlpatterns = [
    path("channels/me", views.my_channel, name="channel-me"),
    path("channels/me/sessions", views.my_sessions, name="channel-sessions"),
    path("channels/me/activity", views.my_activity, name="channel-activity"),
    path("channels/me/overlay/token", views.overlay_token, name="channel-overlay-token"),
    path("channels/me/overlay/test", views.overlay_test, name="channel-overlay-test"),
    path("channels/me/live", views.set_live, name="channel-set-live"),
    path("channels/me/key/rotate", views.rotate_key, name="channel-rotate-key"),
    path("channels/<slug:slug>", views.public_channel, name="channel-public"),
    path("channels/<slug:slug>/status", views.channel_status, name="channel-status"),
    path("channels/me/stream-health", views.stream_health, name="channel-stream-health"),
    path("overlay/<str:token>", views.overlay_info, name="overlay-info"),
    path(
        "webhooks/bunny/stream",
        webhooks.bunny_stream_webhook,
        name="bunny-stream-webhook",
    ),
]
