from django.urls import path

from . import views

urlpatterns = [
    path("register", views.register, name="auth-register"),
    path("login", views.login, name="auth-login"),
    path("2fa/login", views.two_factor_login, name="auth-2fa-login"),
    path("2fa/setup", views.two_factor_setup, name="auth-2fa-setup"),
    path("2fa/enable", views.two_factor_enable, name="auth-2fa-enable"),
    path("2fa/disable", views.two_factor_disable, name="auth-2fa-disable"),
    path("refresh", views.refresh, name="auth-refresh"),
    path("logout", views.logout, name="auth-logout"),
    path("me", views.me, name="auth-me"),
    path("sessions", views.list_sessions, name="auth-sessions"),
    path("sessions/revoke-others", views.revoke_other_sessions, name="auth-sessions-revoke-others"),
    path("sessions/<int:pk>", views.revoke_session, name="auth-session-revoke"),
    path("email/verify", views.email_verify, name="auth-email-verify"),
    path("email/resend", views.email_resend, name="auth-email-resend"),
    path(
        "password/reset/request",
        views.password_reset_request,
        name="auth-password-reset-request",
    ),
    path(
        "password/reset/confirm",
        views.password_reset_confirm,
        name="auth-password-reset-confirm",
    ),
]
