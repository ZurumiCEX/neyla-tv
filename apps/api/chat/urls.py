from django.urls import path

from . import views

urlpatterns = [
    path("c/<slug:slug>/chat/history", views.chat_history, name="chat-history"),
    path("c/me/chat-bans", views.my_chat_bans, name="chat-my-bans"),
    path("c/me/chat-bans/user/<str:username>", views.lift_user_ban, name="chat-lift-user-ban"),
    path("c/me/chat-bans/ip/<str:ip>", views.lift_ip_ban, name="chat-lift-ip-ban"),
]
