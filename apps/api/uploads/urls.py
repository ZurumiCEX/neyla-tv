from django.urls import path

from . import views

urlpatterns = [
    path("uploads/avatar", views.upload_avatar, name="upload-avatar"),
    path("uploads/banner", views.upload_banner, name="upload-banner"),
    path("uploads/game/<slug:slug>", views.upload_game_box_art, name="upload-game"),
]
