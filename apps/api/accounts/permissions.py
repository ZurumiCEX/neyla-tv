"""Permissions DRF basées sur le rôle utilisateur (cf. accounts.User.Role)."""

from __future__ import annotations

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from .models import User


def has_strong_auth(user) -> bool:
    """2FA TOTP active ou au moins une passkey enregistrée."""
    tf = getattr(user, "two_factor", None)
    return bool(tf and tf.enabled) or user.passkeys.exists()


class _RolePermission(BasePermission):
    allowed: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:  # noqa: ARG002
        user = request.user
        ok = bool(
            user and user.is_authenticated and (user.role in self.allowed or user.is_superuser)
        )
        if ok and getattr(settings, "REQUIRE_STAFF_2FA", False) and not has_strong_auth(user):
            raise PermissionDenied(
                {
                    "detail": "Active la double authentification ou une passkey pour "
                    "accéder à la console.",
                    "code": "two_factor_required",
                }
            )
        return ok


class IsAdminRole(_RolePermission):
    allowed = (User.Role.ADMIN,)


class IsModerator(_RolePermission):
    """Modérateur ou admin."""

    allowed = (User.Role.MODERATOR, User.Role.ADMIN)


class IsSupport(_RolePermission):
    """Support, modérateur ou admin (équipe interne)."""

    allowed = (User.Role.SUPPORT, User.Role.MODERATOR, User.Role.ADMIN)
