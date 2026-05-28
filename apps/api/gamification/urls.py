from django.urls import path

from . import views

urlpatterns = [
    path("achievements", views.my_achievements, name="achievements-list"),
]
