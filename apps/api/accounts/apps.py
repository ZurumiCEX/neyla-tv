from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # Enregistre l'export CSV global sur le site admin (tous les modèles).
        from config.admin_actions import register_global_admin_actions

        register_global_admin_actions()
