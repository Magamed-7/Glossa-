import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PlayerRating, RatingHistory

logger = logging.getLogger('ratings')


@receiver(post_save, sender=PlayerRating)
def create_rating_history_on_change(sender, instance, created, **kwargs):
    if created:
        return
    try:
        last_history = RatingHistory.objects.filter(
            player_rating=instance
        ).order_by('-created_at').first()

        score_before = last_history.score_after if last_history else 1000

        if score_before == instance.score:
            return

        change = instance.score - score_before

        RatingHistory.objects.create(
            player_rating=instance,
            score_before=score_before,
            score_after=instance.score,
            change=change,
            reason='duel_win' if change > 0 else 'duel_loss',
        )
        logger.info(
            f'История рейтинга создана: {instance.user.email} | '
            f'{score_before} → {instance.score} ({change:+d})'
        )
    except Exception as e:
        logger.error(f'Ошибка создания истории рейтинга для {instance.user.email}: {e}', exc_info=True)