from django.urls import path

from . import views

urlpatterns = [
    path("discover/live", views.discover_live, name="discover-live"),
    path("discover/categories", views.discover_categories, name="discover-categories"),
    path("discover/groups", views.discover_groups, name="discover-groups"),
    path(
        "discover/categories/<slug:slug>",
        views.discover_category,
        name="discover-category",
    ),
    path("discover/search", views.discover_search, name="discover-search"),
]
