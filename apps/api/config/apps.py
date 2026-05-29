"""AppConfig admin personnalisée pour brancher NeylaAdminSite comme site par défaut."""

from __future__ import annotations

from django.contrib.admin.apps import AdminConfig


class NeylaAdminConfig(AdminConfig):
    default_site = "config.admin_site.NeylaAdminSite"
