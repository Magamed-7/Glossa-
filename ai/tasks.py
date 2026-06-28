import logging
from celery import shared_task
from django.utils import timezone

from users.models import User
from stories.models import Story
from languages.models import Language, CEFRLevel
from .services import AIService


logger = logging.getLogger('ai')


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_story_async(self, user_id, language_code, cefr_level, topic):
    try:
        user = User.objects.get(id=user_id)
        language = Language.objects.get(code=language_code)
        level = CEFRLevel.objects.get(language=language, level=cefr_level)

        ai_service = AIService()
        content = ai_service.generate_story(
            user=user,
            language_code=language_code,
            level_code=cefr_level,
            topic=topic,
        )

        if content:
            Story.objects.create(
                title=f'{topic} ({cefr_level})',
                content=content,
                language=language,
                cefr_level=level,
                topic=topic,
                tags=topic.lower(),
                source='ai_generated',
                status='published',
                is_premium=True,
                read_time_minutes=max(1, len(content.split()) // 200),
                created_by=user,
            )
            logger.info(f'История сгенерирована: {topic} [{cefr_level}] для {user.email}')
        else:
            logger.error(f'Не удалось сгенерировать историю: {topic} [{cefr_level}]')

    except Language.DoesNotExist:
        logger.error(f'Язык не найден: {language_code}')
    except CEFRLevel.DoesNotExist:
        logger.error(f'Уровень не найден: {language_code}/{cefr_level}')
    except User.DoesNotExist:
        logger.error(f'Пользователь не найден: {user_id}')
    except Exception as e:
        logger.error(f'Критическая ошибка generate_story_async: {e}', exc_info=True)
        self.retry(exc=e)
