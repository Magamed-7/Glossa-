from celery import shared_task
from django.utils import timezone
from .models import ReviewSession
import logging

logger = logging.getLogger('learning')


@shared_task
def notify_due_reviews():
    try:
        due_sessions = ReviewSession.objects.filter(
            next_review_at__lte=timezone.now(),
            phrase__is_mastered=False
        ).select_related('phrase__user')

        user_counts = {}
        for session in due_sessions:
            user = session.phrase.user
            user_counts[user] = user_counts.get(user, 0) + 1

        for user, count in user_counts.items():
            try:
                logger.info(f'Пользователь {user.email} — {count} слов к повторению')
            except Exception as e:
                logger.error(f'Ошибка при обработке пользователя {user.email}: {e}',exc_info=True)

    except Exception as e:
        logger.error(f'Критическая ошибка в notify_due_reviews: {e}', exc_info=True)