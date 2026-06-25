from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserPhrase, ReviewSession
import logging

logger = logging.getLogger('learning')

@receiver(post_save, sender=UserPhrase)
def create_review_session(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        if created:
            ReviewSession.objects.create(phrase=instance)
    except Exception as e:
        logger.error(f'Критическая ошибка в чтении фразы: {e}', exc_info=True)