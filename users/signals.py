import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

logger = logging.getLogger('users')


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        Profile.objects.create(user=instance)
        logger.info(f'Профиль создан: {instance.email}')
    except Exception as e:
        logger.error(
            f'Ошибка создания профиля для {instance.email}: {e}', exc_info=True)