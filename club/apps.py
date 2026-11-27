from django.apps import AppConfig


class ClubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "club"

    def ready(self):
        # Switches on the handlers in signals.py (the new-request email to the captain).
        # Imported here, once Django has fully loaded, because signals.py uses the models
        from . import signals  # noqa: F401