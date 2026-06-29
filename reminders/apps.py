from django.apps import AppConfig


class RemindersConfig(AppConfig):
    name = 'reminders'

    def ready(self):
        import reminders.signals  
