from django.urls import path

from . import views

urlpatterns = [
    path("shorts/trending", views.trending, name="shorts-trending"),
    path("shorts/me", views.mine, name="shorts-mine"),
    path("shorts/me/<int:pk>/uploaded", views.mine_uploaded, name="shorts-mine-uploaded"),
    path("shorts/me/<int:pk>", views.mine_delete, name="shorts-mine-delete"),
    path("shorts/<int:pk>", views.detail, name="shorts-detail"),
    path("shorts/<int:pk>/view", views.view, name="shorts-view"),
    path("shorts/<int:pk>/like", views.like, name="shorts-like"),
    path("channels/<slug:slug>/shorts", views.channel_shorts, name="shorts-channel"),
]
