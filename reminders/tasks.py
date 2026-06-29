from celery import shared_task
from django.utils import timezone
import logging
from .models import Reminder, ReminderSchedule
from users.models import User
from learning.models import ReviewSession
from subscriptions.models import Subscription


logger = logging.getLogger('reminders')


@shared_task
def send_daily_review_reminders():
    try:

        schedules = ReminderSchedule.objects.filter(
            is_enabled=True
        ).select_related('user')

        for schedule in schedules:
            try:
                due_count = ReviewSession.objects.filter(
                    phrase__user=schedule.user,
                    next_review_at__lte=timezone.now(),
                    phrase__status='active'
                ).count()

                if due_count == 0:
                    continue

                Reminder.objects.create(
                    user=schedule.user,
                    reminder_type='daily_review',
                    title='Пора повторить слова',
                    body=f'У тебя {due_count} слов ждут повторения. Не теряй прогресс!',
                    scheduled_at=timezone.now(),
                    status='sent',
                    sent_at=timezone.now(),
                )
                logger.info(f'Напоминание отправлено: {schedule.user.email} — {due_count} слов')

            except Exception as e:
                logger.error(f'Ошибка напоминания для {schedule.user.email}: {e}', exc_info=True)

    except Exception as e:
        logger.error(f'Критическая ошибка в send_daily_review_reminders: {e}', exc_info=True)


@shared_task
def send_inactivity_reminders():
    try:

        three_days_ago = timezone.now() - timezone.timedelta(days=3)

        inactive_users = User.objects.filter(
            last_login__lte=three_days_ago,
            is_active=True
        )

        for user in inactive_users:
            try:
                already_sent = Reminder.objects.filter(
                    user=user,
                    reminder_type='inactivity',
                    created_at__gte=three_days_ago
                ).exists()

                if already_sent:
                    continue

                Reminder.objects.create(
                    user=user,
                    reminder_type='inactivity',
                    title='Давно не заходил!',
                    body='Твой прогресс ждёт тебя. Вернись и продолжи изучение языка.',
                    scheduled_at=timezone.now(),
                    status='sent',
                    sent_at=timezone.now(),
                )
                logger.info(f'Напоминание о неактивности: {user.email}')

            except Exception as e:
                logger.error(f'Ошибка напоминания о неактивности для {user.email}: {e}', exc_info=True)

    except Exception as e:
        logger.error(f'Критическая ошибка в send_inactivity_reminders: {e}', exc_info=True)


@shared_task
def send_subscription_expiring_reminders():
    try:

        three_days_later = timezone.now() + timezone.timedelta(days=3)

        expiring = Subscription.objects.filter(
            status='active',
            expires_at__date=three_days_later.date()
        ).select_related('user', 'plan')

        for sub in expiring:
            try:
                Reminder.objects.create(
                    user=sub.user,
                    reminder_type='subscription_expiring',
                    title='Подписка истекает через 3 дня',
                    body=f'Твой тариф {sub.plan.name} истекает {sub.expires_at.strftime("%d.%m.%Y")}. Продли чтобы не потерять доступ.',
                    scheduled_at=timezone.now(),
                    status='sent',
                    sent_at=timezone.now(),
                )
                logger.info(f'Напоминание об истечении подписки: {sub.user.email}')

            except Exception as e:
                logger.error(f'Ошибка напоминания о подписке для {sub.user.email}: {e}', exc_info=True)

    except Exception as e:
        logger.error(f'Критическая ошибка в send_subscription_expiring_reminders: {e}', exc_info=True)