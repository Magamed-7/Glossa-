from celery import shared_task
from django.utils import timezone
from .models import ReviewSession


@shared_task
def notify_due_reviews():
    due_sessions = ReviewSession.objects.filter(
        next_review_at__lte=timezone.now(),
        phrase__is_mastered=False
    ).select_related('phrase__user')

    user_counts = {}
    for session in due_sessions:
        user = session.phrase.user
        user_counts[user] = user_counts.get(user, 0) + 1

    for user, count in user_counts.items():
        print(f'{user.email} — {count} слов к повторению')