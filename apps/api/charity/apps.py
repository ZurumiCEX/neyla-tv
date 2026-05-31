from django.apps import AppConfig


class CharityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "charity"
    verbose_name = "Charity Day & RSE"

    def ready(self) -> None:
        # Branche les signaux (mirroring CharityEvent → PlatformEvent).
        from . import signals  # noqa: F401
