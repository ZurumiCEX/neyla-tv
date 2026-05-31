from django.urls import path

from . import views

urlpatterns = [
    path("achievements", views.my_achievements, name="achievements-list"),
    path("achievements/<str:username>", views.user_achievements, name="achievements-user"),
]
