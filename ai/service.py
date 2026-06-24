import time
import logging
from django.core.cache import cache
from django.conf import settings
import anthropic

logger = logging.getLogger('ai')

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _make_request(user, request_type, prompt, cache_key=None):
    from .models import AIRequestLog

    if cache_key:
        cached = cache.get(cache_key)
        if cached:
            AIRequestLog.objects.create(
                user=user,
                request_type=request_type,
                prompt=prompt,
                response=cached,
                status='cached',
                tokens_used=0,
                response_time_ms=0,
            )
            logger.info(f'AI ответ из кэша: {request_type} | пользователь: {user.email if user else "system"}')
            return cached

    start = time.time()
    try:
        message = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}]
        )
        response_text = message.content[0].text
        elapsed = int((time.time() - start) * 1000)

        AIRequestLog.objects.create(
            user=user,
            request_type=request_type,
            prompt=prompt,
            response=response_text,
            status='success',
            tokens_used=message.usage.input_tokens + message.usage.output_tokens,
            response_time_ms=elapsed,
        )

        if cache_key:
            cache.set(cache_key, response_text, timeout=60 * 60 * 24)

        logger.info(
            f'AI запрос успешен: {request_type} | '
            f'токены: {message.usage.input_tokens + message.usage.output_tokens} | '
            f'время: {elapsed}мс'
        )
        return response_text

    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        AIRequestLog.objects.create(
            user=user,
            request_type=request_type,
            prompt=prompt,
            response='',
            status='failed',
            error_message=str(e),
            response_time_ms=elapsed,
        )
        logger.error(f'Ошибка AI запроса {request_type}: {e}', exc_info=True)
        return None


def generate_story(user, language, cefr_level, topic):
    prompt = (
        f'Напиши короткую историю на языке: {language}. '
        f'Уровень сложности: {cefr_level}. '
        f'Тема: {topic}. '
        f'Длина: 150-200 слов. '
        f'Только текст истории без заголовка и пояснений.'
    )
    cache_key = f'ai_story_{language}_{cefr_level}_{topic}'
    return _make_request(user, 'generate_story', prompt, cache_key)


def explain_word(user, word, language, context_sentence):
    prompt = (
        f'Объясни слово "{word}" на языке {language}. '
        f'Контекст: "{context_sentence}". '
        f'Дай: 1) перевод 2) часть речи 3) пример использования. '
        f'Ответ короткий, без лишних слов.'
    )
    cache_key = f'ai_word_{language}_{word}'
    return _make_request(user, 'explain_word', prompt, cache_key)


def explain_grammar(user, rule, language, cefr_level):
    prompt = (
        f'Объясни грамматическое правило "{rule}" для языка {language}. '
        f'Уровень студента: {cefr_level}. '
        f'Дай: 1) простое объяснение 2) два живых примера предложений. '
        f'Ответ короткий и понятный.'
    )
    cache_key = f'ai_grammar_{language}_{cefr_level}_{rule}'
    return _make_request(user, 'explain_grammar', prompt, cache_key)


def generate_duel_question(user, language, cefr_level, round_type):
    prompt = (
        f'Создай один вопрос для дуэли по языку {language}, уровень {cefr_level}. '
        f'Тип вопроса: {round_type}. '
        f'Верни строго в формате JSON: '
        f'{{"question": "...", "correct_answer": "...", "options": ["...", "...", "...", "..."]}}'
    )
    return _make_request(user, 'generate_question', prompt)