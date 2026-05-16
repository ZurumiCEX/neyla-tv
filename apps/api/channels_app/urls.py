from django.urls import path

from . import views, webhooks

urlpatterns = [
    path("channels/me", views.my_channel, name="channel-me"),
    path("channels/me/key/rotate", views.rotate_key, name="channel-rotate-key"),
    path("channels/<slug:slug>", views.public_channel, name="channel-public"),
    path("channels/<slug:slug>/status", views.channel_status, name="channel-status"),
    path(
        "webhooks/cloudflare/stream",
        webhooks.cloudflare_stream_webhook,
        name="cloudflare-stream-webhook",
    ),
]
