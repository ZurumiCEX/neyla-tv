"""Actions et utilitaires partagés du Django admin (export CSV global, etc.)."""

from __future__ import annotations

import csv

from django.http import HttpResponse


def export_as_csv(modeladmin, request, queryset):  # noqa: ARG001
    """Exporte la sélection en CSV (disponible sur tous les modèles enregistrés)."""
    meta = modeladmin.model._meta
    field_names = [f.name for f in meta.fields]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={meta.app_label}_{meta.model_name}.csv"
    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in queryset.iterator():
        writer.writerow([getattr(obj, name) for name in field_names])
    return response


export_as_csv.short_description = "Exporter la sélection en CSV"


def register_global_admin_actions() -> None:
    """Ajoute les actions globales au site admin (idempotent)."""
    from django.contrib import admin

    admin.site.add_action(export_as_csv, "export_as_csv")
