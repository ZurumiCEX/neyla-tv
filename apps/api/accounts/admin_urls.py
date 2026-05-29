from django.urls import path

from . import admin_views, views

urlpatterns = [
    path("admin/users", admin_views.AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>", admin_views.admin_user_detail, name="admin-user-detail"),
    path("guides/progress", views.guide_progress, name="guides-progress"),
]
