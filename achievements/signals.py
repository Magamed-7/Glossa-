import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('achievements')


@receiver(post_save, sender='learning.UserPhrase')
def on_user_phrase(sender, instance, created, **kwargs):
    if created:
        try:
            from .services import check_achievements
            check_achievements(instance.user)
        except Exception as e:
            logger.error(f'Ошибка check_achievements после UserPhrase: {e}', exc_info=True)


@receiver(post_save, sender='learning.ReviewSession')
def on_review_session(sender, instance, **kwargs):
    try:
        from .services import check_achievements
        check_achievements(instance.phrase.user)
    except Exception as e:
        logger.error(f'Ошибка check_achievements после ReviewSession: {e}', exc_info=True)


@receiver(post_save, sender='duels.DuelResult')
def on_duel_result(sender, instance, created, **kwargs):
    if created:
        try:
            from .services import check_achievements
            duel = instance.duel
            if duel.player_one:
                check_achievements(duel.player_one)
            if duel.player_two:
                check_achievements(duel.player_two)
        except Exception as e:
            logger.error(f'Ошибка check_achievements после DuelResult: {e}', exc_info=True)


@receiver(post_save, sender='stories.Story')
def on_story(sender, instance, created, **kwargs):
    if created:
        try:
            from .services import check_achievements
            check_achievements(instance.created_by)
        except Exception as e:
            logger.error(f'Ошибка check_achievements после Story: {e}', exc_info=True)


@receiver(post_save, sender='grammar.GrammarLesson')
def on_grammar_lesson(sender, instance, **kwargs):
    try:
        from .services import check_achievements
        # user передаётся через контекст, если нет — пропускаем
    except Exception as e:
        logger.error(f'Ошибка check_achievements после GrammarLesson: {e}', exc_info=True)