import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DuelResult
from ratings.models import PlayerRating

logger = logging.getLogger('duels')


@receiver(post_save, sender=DuelResult)
def update_ratings_on_duel_finish(sender, instance, created, **kwargs):
    if not created:
        return
    try:

        duel = instance.duel
        if duel.mode != 'rated':
            return

        for player, change in [
            (duel.player_one, instance.rating_change_player_one),
            (duel.player_two, instance.rating_change_player_two),
        ]:
            if player is None:
                continue
            try:
                rating, _ = PlayerRating.objects.get_or_create(
                    user=player,
                    language=duel.language,
                    defaults={'score': 1000}
                )
                rating.score += change
                rating.total_duels += 1
                if duel.winner == player:
                    rating.wins += 1
                elif duel.status != 'draw':
                    rating.losses += 1
                rating.save()
                logger.info(
                    f'Рейтинг обновлён: {player.email} | изменение: {change:+d} | новый рейтинг: {rating.score}'
                )
            except Exception as e:
                logger.error(f'Ошибка обновления рейтинга для {player.email}: {e}', exc_info=True)

    except Exception as e:
        logger.error(f'Критическая ошибка в update_ratings_on_duel_finish: {e}', exc_info=True)