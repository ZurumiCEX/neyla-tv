from django.urls import path

from . import views

urlpatterns = [
    path("reports", views.create_report, name="reports-create"),
    path("moderation/reports", views.ReportListView.as_view(), name="moderation-reports"),
    path("moderation/reports/<int:pk>", views.report_detail, name="moderation-report-detail"),
    path(
        "moderation/banned-words/import",
        views.import_banned_words,
        name="moderation-banned-words-import",
    ),
]
