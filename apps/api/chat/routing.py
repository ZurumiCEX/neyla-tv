from django.urls import path

from .consumers import ChatConsumer, OverlayConsumer

websocket_urlpatterns = [
    path("ws/c/<slug:slug>/chat", ChatConsumer.as_asgi()),
    path("ws/overlay/<str:token>", OverlayConsumer.as_asgi()),
]
