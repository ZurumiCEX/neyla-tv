from django.urls import path

from . import views

urlpatterns = [
    path("invites", views.invites, name="invites"),
]
