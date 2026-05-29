from django.urls import path

from . import views

urlpatterns = [
    path("collaborations", views.collaborations, name="collaborations"),
    path("collaborations/<int:pk>", views.collaboration_detail, name="collaboration-detail"),
    path("follows/me", views.my_followings, name="follows-me"),
    path("follows/<slug:username>", views.follow_endpoint, name="follows-target"),
    path(
        "follows/<slug:username>/status",
        views.follow_status,
        name="follows-status",
    ),
]
