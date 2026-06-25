import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserStoryProgress

logger = logging.getLogger('stories')


@receiver(post_save, sender=UserStoryProgress)
def increment_story_views(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        instance.story.views_count += 1
        instance.story.save(update_fields=['views_count'])
        logger.info(f'Просмотр засчитан: {instance.user.email} — {instance.story.title}')
    except Exception as e:
        logger.error(
            f'Ошибка increment_story_views для {instance.user.email}: {e}', exc_info=True)