from django.urls import path

from . import views

urlpatterns = [
    path("streamer/apply", views.submit, name="streamer-apply"),
    path("streamer/application", views.my_application, name="streamer-application"),
]
