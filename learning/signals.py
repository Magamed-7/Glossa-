from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserPhrase, ReviewSession


@receiver(post_save, sender=UserPhrase)
def create_review_session(sender, instance, created, **kwargs):
    if created:
        ReviewSession.objects.create(phrase=instance)