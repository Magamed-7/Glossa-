from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserStoryProgress


@receiver(post_save, sender=UserStoryProgress)
def increment_story_views(sender, instance, created, **kwargs):
    if created:
        instance.story.views_count += 1
        instance.story.save(update_fields=['views_count'])