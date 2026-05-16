"""Tâches Celery : envoi d'emails transactionnels (verify, reset)."""

from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import User
from .tokens import (
    EMAIL_VERIFY_PURPOSE,
    PASSWORD_RESET_PURPOSE,
    make_token,
)


@shared_task
def send_email_verification(user_id: int) -> None:
    user = User.objects.filter(pk=user_id).first()
    if user is None or user.is_email_verified:
        return
    token = make_token(user.pk, EMAIL_VERIFY_PURPOSE)
    body = render_to_string(
        "accounts/emails/verify_email.txt",
        {"user": user, "token": token, "frontend_url": settings.FRONTEND_URL},
    )
    send_mail(
        subject="Vérifie ton adresse email — Neyla TV",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


@shared_task
def send_password_reset(user_id: int) -> None:
    user = User.objects.filter(pk=user_id).first()
    if user is None:
        return
    token = make_token(user.pk, PASSWORD_RESET_PURPOSE)
    body = render_to_string(
        "accounts/emails/password_reset.txt",
        {"user": user, "token": token, "frontend_url": settings.FRONTEND_URL},
    )
    send_mail(
        subject="Réinitialise ton mot de passe — Neyla TV",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
