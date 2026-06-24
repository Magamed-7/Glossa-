from celery import shared_task
import logging
from users.models import User
from stories.models import Story
from languages.models import Language, CEFRLevel
from .service import generate_story


logger = logging.getLogger('ai')


@shared_task
def generate_story_async(user_id, language_code, cefr_level, topic):
    try:

        user = User.objects.get(id=user_id)
        language = Language.objects.get(code=language_code)
        level = CEFRLevel.objects.get(language=language, level=cefr_level)

        content = generate_story(user, language.name, cefr_level, topic)

        if content:
            Story.objects.create(
                title=f'{topic} ({cefr_level})',
                content=content,
                language=language,
                cefr_level=level,
                topic=topic,
                source='ai_generated',
                status='published',
                is_premium=True,
                created_by=user,
            )
            logger.info(f'История сгенерирована: {topic} [{cefr_level}] для {user.email}')
        else:
            logger.error(f'Не удалось сгенерировать историю: {topic} [{cefr_level}]', exc_info=True)

    except Exception as e:
        logger.error(f'Критическая ошибка generate_story_async: {e}', exc_info=True)