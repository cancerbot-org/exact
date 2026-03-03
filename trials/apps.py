from django.apps import AppConfig


class TrialsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trials'

    def ready(self):
        import trials.signals  # noqa: F401 — register signal handlers
