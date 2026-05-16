from django.apps import AppConfig


class ChannelsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "channels_app"
    verbose_name = "Channels (streamer)"

    def ready(self) -> None:
        # Import des signaux pour les enregistrer auprès de Django.
        from . import signals  # noqa: F401
