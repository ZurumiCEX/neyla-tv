from django.urls import path

from . import views

urlpatterns = [
    path("announcements/active", views.active, name="announcements-active"),
]
