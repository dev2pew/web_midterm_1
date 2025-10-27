from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # IMPORT SIGNALS TO AUTO-CREATE PROFILE ON USER CREATION

        from . import signals  # NOQA: F401
