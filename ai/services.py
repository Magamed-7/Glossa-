import json
import time
import random
import logging
from functools import lru_cache

from django.conf import settings
from django.core.cache import cache
from .models import AIRequestLog

logger = logging.getLogger('ai')


def _pick_key(keys_list):
    if not keys_list:
        return None
    return random.choice(keys_list)


@lru_cache(maxsize=1)
def get_anthropic_client():
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or _pick_key(getattr(settings, 'CLAUDE_API_KEYS', []))
    if not api_key:
        return None
    from anthropic import Anthropic
    return Anthropic(api_key=api_key)


@lru_cache(maxsize=1)
def get_openai_client():
    keys = getattr(settings, 'OPENAI_API_KEYS', [])
    if not keys:
        return None
    from openai import OpenAI
    return OpenAI(api_key=keys[0])


@lru_cache(maxsize=1)
def get_gemini_model():
    keys = getattr(settings, 'GEMINI_API_KEYS', [])
    if not keys:
        return None
    import google.generativeai as genai
    genai.configure(api_key=keys[0])
    return genai.GenerativeModel('gemini-2.0-flash')


@lru_cache(maxsize=1)
def get_groq_client():
    keys = getattr(settings, 'GROQ_API_KEYS', [])
    if not keys:
        return None
    from groq import Groq
    return Groq(api_key=keys[0])


@lru_cache(maxsize=1)
def get_deepseek_client():
    keys = getattr(settings, 'DEEPSEEK_API_KEYS', [])
    if not keys:
        return None
    from openai import OpenAI
    return OpenAI(api_key=keys[0], base_url='https://api.deepseek.com')


def _call_ai(system_prompt, user_prompt, max_tokens=1024):
    providers = ['anthropic', 'openai', 'groq', 'deepseek', 'gemini']
    random.shuffle(providers)

    for provider in providers:
        try:
            result = None
            if provider == 'anthropic':
                client = get_anthropic_client()
                if client:
                    message = client.messages.create(
                        model=getattr(settings, 'AI_MODEL', 'claude-sonnet-4-20250514'),
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=[{'role': 'user', 'content': user_prompt}],
                    )
                    result = message.content[0].text

            elif provider == 'openai':
                client = get_openai_client()
                if client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        max_tokens=max_tokens,
                        messages=[
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt},
                        ],
                    )
                    result = resp.choices[0].message.content

            elif provider == 'groq':
                client = get_groq_client()
                if client:
                    resp = client.chat.completions.create(
                        model='llama-3.3-70b-versatile',
                        max_tokens=max_tokens,
                        messages=[
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt},
                        ],
                    )
                    result = resp.choices[0].message.content

            elif provider == 'deepseek':
                client = get_deepseek_client()
                if client:
                    resp = client.chat.completions.create(
                        model='deepseek-chat',
                        max_tokens=max_tokens,
                        messages=[
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt},
                        ],
                    )
                    result = resp.choices[0].message.content

            elif provider == 'gemini':
                model = get_gemini_model()
                if model:
                    resp = model.generate_content(
                        f'{system_prompt}\n\n{user_prompt}',
                        generation_config={'max_output_tokens': max_tokens},
                    )
                    result = resp.text

            if result:
                logger.info(f'AI ответ получен через {provider}')
                return result

        except Exception as e:
            logger.warning(f'AI провайдер {provider} ошибка: {e}')
            continue

    logger.error('Все AI провайдеры недоступны')
    return None


class AIService:

    def _log_request(self, user, request_type, prompt, response, status='success', error_message='', tokens=100, duration_ms=250):
        try:
            AIRequestLog.objects.create(
                user=user,
                request_type=request_type,
                prompt=prompt,
                response=response,
                status=status,
                error_message=error_message,
                tokens_used=tokens,
                response_time_ms=duration_ms,
            )
        except Exception as e:
            logger.error(f'Ошибка записи лога AI запроса: {e}')

    def generate_story(self, user, language_code, level_code, topic):
        start_time = time.time()
        cache_key = f'ai_story_{language_code}_{level_code}_{topic}'
        cached = cache.get(cache_key)
        if cached:
            self._log_request(user=user, request_type='generate_story', prompt=f'{language_code}/{level_code}/{topic}', response=cached, status='cached', duration_ms=1)
            return cached

        system_prompt = (
            f'You are a language learning content creator. Write a short story in {language_code} '
            f'at CEFR level {level_code} about the topic: {topic}. '
            f'The story should be engaging, educational, and appropriate for the target level. '
            f'Return only the story text, no title or metadata.'
        )
        user_prompt = f'Write a {level_code} level story in {language_code} about {topic}.'

        ai_response = _call_ai(system_prompt, user_prompt, max_tokens=2048)

        if not ai_response:
            ai_response = f'Mock story in {language_code} ({level_code}) about {topic}. Once upon a time...'

        duration = int((time.time() - start_time) * 1000)
        self._log_request(user=user, request_type='generate_story', prompt=user_prompt, response=ai_response, duration_ms=duration)
        cache.set(cache_key, ai_response, 24 * 60 * 60)
        return ai_response

    def assist_story_creation(self, user, text, target_level, language_code):
        start_time = time.time()
        system_prompt = (
            f'You are an AI writing assistant for language learners. The user is writing a story in {language_code} '
            f'targeted at CEFR level {target_level}. '
            f'Improve the text: fix grammar, adapt vocabulary to the target level, suggest better phrasing. '
            f"Return a JSON object with keys: 'improved_text', 'suggested_title', 'tags' (list of strings), "
            f"'word_markup' (list of objects with 'word', 'translation', 'part_of_speech', 'context_sentence')."
        )
        user_prompt = f'Improve and adapt this text to {target_level} level:\n\n{text}'

        ai_response = _call_ai(system_prompt, user_prompt, max_tokens=2048)

        if not ai_response:
            ai_response = json.dumps({
                'improved_text': text,
                'suggested_title': '',
                'tags': [],
                'word_markup': [],
            })
        else:
            try:
                parsed = json.loads(ai_response)
                ai_response = json.dumps(parsed)
            except (json.JSONDecodeError, TypeError):
                ai_response = json.dumps({
                    'improved_text': ai_response,
                    'suggested_title': '',
                    'tags': [],
                    'word_markup': [],
                })

        duration = int((time.time() - start_time) * 1000)
        self._log_request(user=user, request_type='assist_story_creation', prompt=user_prompt, response=ai_response, duration_ms=duration)
        return ai_response

    def explain_word(self, user, word, context, language_code):
        start_time = time.time()
        cache_key = f'ai_explain_{language_code}_{word}_{hash(context)}'
        cached = cache.get(cache_key)
        if cached:
            self._log_request(user=user, request_type='explain_word', prompt=f'{word}/{context}', response=cached, status='cached', duration_ms=1)
            return cached

        system_prompt = (
            f"You are a language tutor. Explain the word '{word}' as used in the context "
            f"'{context}' for a {language_code} language learner. "
            f'Include: translation, part of speech, usage notes, and 2 example sentences. '
            f"Return a JSON object with keys: 'translation', 'part_of_speech', 'explanation', 'examples' (list of strings)."
        )
        user_prompt = f"Explain the word '{word}' in context: '{context}'"

        ai_response = _call_ai(system_prompt, user_prompt, max_tokens=512)

        if not ai_response:
            ai_response = json.dumps({
                'translation': word,
                'part_of_speech': 'unknown',
                'explanation': f'Mock explanation of "{word}" in this context.',
                'examples': [context],
            })
        else:
            try:
                parsed = json.loads(ai_response)
                ai_response = json.dumps(parsed)
            except (json.JSONDecodeError, TypeError):
                ai_response = json.dumps({
                    'translation': word,
                    'part_of_speech': 'unknown',
                    'explanation': ai_response,
                    'examples': [],
                })

        duration = int((time.time() - start_time) * 1000)
        self._log_request(user=user, request_type='explain_word', prompt=user_prompt, response=ai_response, duration_ms=duration)
        cache.set(cache_key, ai_response, 24 * 60 * 60)
        return ai_response

    def generate_duel_question(self, user, level_code, language_code, category):
        start_time = time.time()
        system_prompt = (
            f"You are a language quiz generator. Create a single multiple-choice question for a {language_code} "
            f"learner at CEFR level {level_code} in the category '{category}'. "
            f'Question types: translate_word, choose_form, build_sentence, fill_blank. '
            f"Return a JSON object with keys: 'question_type', 'question' (text), "
            f"'options' (list of 4 strings), 'correct_answer' (string, must be one of the options)."
        )
        user_prompt = f'Generate a {level_code} level {language_code} question about {category}.'

        ai_response = _call_ai(system_prompt, user_prompt, max_tokens=512)

        if not ai_response:
            result = {
                'question_type': 'translate_word',
                'question': f'How do you say "hello" in {language_code}?',
                'options': ['hello', 'goodbye', 'thank you', 'please'],
                'correct_answer': 'hello',
            }
        else:
            try:
                result = json.loads(ai_response)
            except (json.JSONDecodeError, TypeError):
                result = {
                    'question_type': 'translate_word',
                    'question': ai_response[:200],
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 'A',
                }

        duration = int((time.time() - start_time) * 1000)
        self._log_request(user=user, request_type='generate_duel_question', prompt=user_prompt, response=json.dumps(result), duration_ms=duration)
        return result

    def ai_duel_answer(self, user, question, options, level_code):
        start_time = time.time()

        system_prompt = (
            f'You are an AI language learner at CEFR level {level_code} participating in a quiz duel. '
            f'Sometimes you answer correctly, sometimes you make mistakes to keep the game fun. '
            f'Return only one of the option strings, nothing else.'
        )
        user_prompt = f'Question: {question}\nOptions: {json.dumps(options)}\nYour answer:'

        ai_response = _call_ai(system_prompt, user_prompt, max_tokens=32)

        if ai_response and ai_response.strip() in options:
            answer = ai_response.strip()
        else:
            weights = [0.7, 0.1, 0.1, 0.1]
            if len(options) > 1:
                answer = random.choices(options, weights=weights[:len(options)])[0]
            else:
                answer = options[0] if options else ''

        duration = int((time.time() - start_time) * 1000)
        self._log_request(
            user=user, request_type='ai_duel_answer',
            prompt=f'{question} | {json.dumps(options)}',
            response=answer, duration_ms=duration,
        )
        return answer