import logging
from django.db.models import Q

from .models import Achievement, UserAchievement

logger = logging.getLogger('achievements')


def _has(user, code):
    return UserAchievement.objects.filter(user=user, achievement__code=code).exists()


def _award(user, code):
    if _has(user, code):
        return False
    try:
        achievement = Achievement.objects.get(code=code)
        UserAchievement.objects.create(user=user, achievement=achievement)
        logger.info(f'Достижение "{achievement.title}" выдано пользователю {user.email}')
        return True
    except Achievement.DoesNotExist:
        logger.warning(f'Достижение с кодом "{code}" не найдено в БД')
        return False


def _get_value(user, field_name, default=0):
    try:
        return getattr(user, field_name, default) or default
    except Exception:
        return default


def _count_qs(qs):
    try:
        return qs.count()
    except Exception:
        return 0


def check_achievements(user):
    try:
        _check_cEFR_levels(user)
        _check_reading(user)
        _check_vocabulary(user)
        _check_reviews(user)
        _check_streaks(user)
        _check_duels(user)
        _check_rating(user)
        _check_grammar(user)
        _check_languages(user)
    except Exception as e:
        logger.error(f'Ошибка в check_achievements для {user.email}: {e}', exc_info=True)


def _check_cEFR_levels(user):
    try:
        from learning.models import UserPhrase
        levels_done = UserPhrase.objects.filter(user=user).values_list('language__cefr_levels', flat=True).distinct().count()
        if levels_done >= 1:
            _award(user, 'first_step')
        if levels_done >= 2:
            _award(user, 'beginner')
        if levels_done >= 3:
            _award(user, 'elementary')
        if levels_done >= 4:
            _award(user, 'intermediate')
        if levels_done >= 5:
            _award(user, 'upper_intermediate')
        if levels_done >= 6:
            _award(user, 'advanced')
    except Exception as e:
        logger.error(f'Ошибка _check_cEFR_levels: {e}', exc_info=True)


def _check_reading(user):
    try:
        from stories.models import Story
        total_stories = _count_qs(Story.objects.filter(Q(created_by=user) | Q(user_progress__user=user)))
        if total_stories >= 1:
            _award(user, 'first_story')
        if total_stories >= 50:
            _award(user, 'bookworm')
        if total_stories >= 200:
            _award(user, 'librarian')
        authored = _count_qs(Story.objects.filter(created_by=user))
        if authored >= 1:
            _award(user, 'author')
        if authored >= 10:
            _award(user, 'storyteller')
        featured = _count_qs(Story.objects.filter(created_by=user, is_featured=True))
        if featured >= 1:
            _award(user, 'featured')
    except Exception as e:
        logger.error(f'Ошибка _check_reading: {e}', exc_info=True)


def _check_vocabulary(user):
    try:
        from learning.models import UserPhrase
        total_words = _count_qs(UserPhrase.objects.filter(user=user))
        if total_words >= 1:
            _award(user, 'first_word')
        if total_words >= 100:
            _award(user, 'collector')
        if total_words >= 500:
            _award(user, 'vocabulary')
        if total_words >= 1000:
            _award(user, 'wordsmith')
        if total_words >= 2000:
            _award(user, 'lexicon')
        mastered = _count_qs(UserPhrase.objects.filter(user=user, status='mastered'))
        if mastered >= 1:
            _award(user, 'first_mastered')
        if mastered >= 100:
            _award(user, 'mastery_100')
        if mastered >= 500:
            _award(user, 'mastery_500')
    except Exception as e:
        logger.error(f'Ошибка _check_vocabulary: {e}', exc_info=True)


def _check_reviews(user):
    try:
        from learning.models import ReviewSession
        total_reviews = _count_qs(ReviewSession.objects.filter(phrase__user=user))
        if total_reviews >= 1:
            _award(user, 'first_review')
        if total_reviews >= 100:
            _award(user, 'flow_state')
    except Exception as e:
        logger.error(f'Ошибка _check_reviews: {e}', exc_info=True)


def _check_streaks(user):
    try:
        from users.models import Profile
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return
        best_streak = getattr(profile, 'best_streak', 0) or 0
        if best_streak >= 3:
            _award(user, 'on_fire')
        if best_streak >= 7:
            _award(user, 'week_warrior')
        if best_streak >= 14:
            _award(user, 'two_weeks')
        if best_streak >= 30:
            _award(user, 'monthly')
        if best_streak >= 60:
            _award(user, 'unstoppable')
        if best_streak >= 100:
            _award(user, 'legendary')
        if best_streak >= 365:
            _award(user, 'immortal')
    except Exception as e:
        logger.error(f'Ошибка _check_streaks: {e}', exc_info=True)


def _check_duels(user):
    try:
        from duels.models import Duel
        total_duels = _count_qs(
            Duel.objects.filter(Q(player_one=user) | Q(player_two=user), status='finished'))
        if total_duels >= 1:
            _award(user, 'first_duel')
        if total_duels >= 10:
            _award(user, 'fighter')
        if total_duels >= 50:
            _award(user, 'veteran')
        if total_duels >= 100:
            _award(user, 'champion')
        wins = _count_qs(Duel.objects.filter(winner=user, status='finished'))
        if wins >= 1:
            _award(user, 'first_win')
        if wins >= 20:
            _award(user, 'undefeated')
    except Exception as e:
        logger.error(f'Ошибка _check_duels: {e}', exc_info=True)


def _check_rating(user):
    try:
        from ratings.models import PlayerRating
        ratings = PlayerRating.objects.filter(user=user)
        if ratings.exists():
            _award(user, 'ranked')
        for r in ratings:
            if r.score >= 1200:
                _award(user, 'bronze')
            if r.score >= 1500:
                _award(user, 'silver')
            if r.score >= 2000:
                _award(user, 'gold')
            if r.score >= 2500:
                _award(user, 'diamond')
            if r.score >= 3000:
                _award(user, 'grandmaster')
    except Exception as e:
        logger.error(f'Ошибка _check_rating: {e}', exc_info=True)


def _check_grammar(user):
    try:
        from grammar.models import UserGrammarProgress
        completed = _count_qs(UserGrammarProgress.objects.filter(user=user, status='completed'))
        if completed >= 1:
            _award(user, 'grammar_rookie')
        if completed >= 20:
            _award(user, 'grammar_pro')
    except Exception as e:
        logger.error(f'Ошибка _check_grammar: {e}', exc_info=True)


def _check_languages(user):
    try:
        from users.models import UserLanguage
        lang_count = _count_qs(UserLanguage.objects.filter(user=user))
        if lang_count >= 2:
            _award(user, 'polyglot')
        if lang_count >= 3:
            _award(user, 'multilingual')
    except Exception as e:
        logger.error(f'Ошибка _check_languages: {e}', exc_info=True)