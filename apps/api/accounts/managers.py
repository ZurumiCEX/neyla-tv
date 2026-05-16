"""Manager User avec email comme identifiant unique (pas de username Django)."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager["User"]):  # type: ignore[name-defined]
    use_in_migrations = True

    def _create_user(self, email: str, username: str, password: str | None, **extra: Any) -> Any:
        if not email:
            raise ValueError("L'email est obligatoire.")
        if not username:
            raise ValueError("Le username est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username.lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, username: str, password: str | None = None, **extra: Any
    ) -> Any:
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra)

    def create_superuser(
        self, email: str, username: str, password: str | None = None, **extra: Any
    ) -> Any:
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser doit avoir is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser doit avoir is_superuser=True.")
        return self._create_user(email, username, password, **extra)
