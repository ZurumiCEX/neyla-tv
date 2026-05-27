"""Permissions DRF basées sur le rôle utilisateur (cf. accounts.User.Role)."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from .models import User


class _RolePermission(BasePermission):
    allowed: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:  # noqa: ARG002
        user = request.user
        return bool(
            user and user.is_authenticated and (user.role in self.allowed or user.is_superuser)
        )


class IsAdminRole(_RolePermission):
    allowed = (User.Role.ADMIN,)


class IsModerator(_RolePermission):
    """Modérateur ou admin."""

    allowed = (User.Role.MODERATOR, User.Role.ADMIN)


class IsSupport(_RolePermission):
    """Support, modérateur ou admin (équipe interne)."""

    allowed = (User.Role.SUPPORT, User.Role.MODERATOR, User.Role.ADMIN)
