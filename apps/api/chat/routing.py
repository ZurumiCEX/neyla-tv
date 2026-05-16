from django.urls import path

from .consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/c/<slug:slug>/chat", ChatConsumer.as_asgi()),
]
