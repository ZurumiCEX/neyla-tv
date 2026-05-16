from django.urls import path

from . import views

urlpatterns = [
    path("c/<slug:slug>/chat/history", views.chat_history, name="chat-history"),
]
