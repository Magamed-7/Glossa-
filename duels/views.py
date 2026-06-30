import logging

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from ai.services import AIService

from languages.models import Language, CEFRLevel

from .models import Duel, DuelRound, DuelResult
from .serializers import (
    DuelDetailSerializer,
    DuelListSerializer,
    CreateDuelSerializer,
    DuelResultWithRecommendationSerializer,
)

logger = logging.getLogger('duels')


def _has_active_pro(user):
    sub = (
        user.subscriptions
        .filter(status='active')
        .select_related('plan')
        .order_by('-created_at')
        .first()
    )
    if not sub:
        return False
    return sub.is_active and sub.plan.full_catalog_access


def _resolve_language_and_level(language_code, cefr_level):
    try:
        language = Language.objects.get(code=language_code, is_active=True)
    except Language.DoesNotExist:
        return None, None, 'Язык не найден или неактивен.'
    try:
        level = CEFRLevel.objects.get(language=language, level=cefr_level)
    except CEFRLevel.DoesNotExist:
        return None, None, 'Уровень CEFR не найден для данного языка.'
    return language, level, None


def _build_round_for_duel(duel, round_number, category='translate_word'):
    question_data = AIService().generate_duel_question(
        user=duel.player_one,
        level_code=duel.cefr_level.level,
        language_code=duel.language.code,
        category=category,
    )
    return DuelRound.objects.create(
        duel=duel,
        round_number=round_number,
        round_type=question_data.get('question_type', 'translate_word'),
        question_text=question_data.get('question', ''),
        options=question_data.get('options', []),
        correct_answer=question_data.get('correct_answer', ''),
    )


def _finalize_round(round_obj):
    if round_obj.round_winner_id is not None or round_obj.is_draw:
        return round_obj

    duel = round_obj.duel
    p1 = round_obj.answer_player_one
    p2 = round_obj.answer_player_two
    p1_correct = bool(p1) and p1.lower() == round_obj.correct_answer.lower()
    p2_correct = bool(p2) and p2.lower() == round_obj.correct_answer.lower()

    if p1_correct and not p2_correct:
        round_obj.round_winner = duel.player_one
    elif p2_correct and not p1_correct:
        round_obj.round_winner = duel.player_two
    elif p1_correct and p2_correct:
        if round_obj.time_player_one is not None and round_obj.time_player_two is not None:
            if round_obj.time_player_one <= round_obj.time_player_two:
                round_obj.round_winner = duel.player_one
            else:
                round_obj.round_winner = duel.player_two
        else:
            round_obj.is_draw = True
    else:
        round_obj.is_draw = True

    if not round_obj.finished_at:
        round_obj.finished_at = timezone.now()
    round_obj.save()
    return round_obj


def _get_rating_score(user, language):
    from ratings.models import PlayerRating
    rating, _ = PlayerRating.objects.get_or_create(
        user=user, language=language, defaults={'score': 1000}
    )
    return rating.score


def _finalize_duel(duel):
    existing = getattr(duel, 'result', None)
    if duel.status == 'finished' and existing:
        return existing

    for rnd in duel.rounds.all():
        _finalize_round(rnd)

    score_one = duel.rounds.filter(round_winner=duel.player_one).count()
    score_two = duel.rounds.filter(round_winner=duel.player_two).count()

    if score_one > score_two:
        duel.winner = duel.player_one
        duel.is_draw = False
    elif score_two > score_one:
        duel.winner = duel.player_two
        duel.is_draw = False
    else:
        duel.winner = None
        duel.is_draw = True

    duel.status = 'finished'
    duel.finished_at = timezone.now()
    duel.save()

    avg_one = None
    avg_two = None
    times_one = [r.time_player_one for r in duel.rounds.all() if r.time_player_one is not None]
    times_two = [r.time_player_two for r in duel.rounds.all() if r.time_player_two is not None]
    if times_one:
        avg_one = round(sum(times_one) / len(times_one), 2)
    if times_two:
        avg_two = round(sum(times_two) / len(times_two), 2)

    rating_one = 0
    rating_two = 0
    if duel.mode == 'rated' and duel.opponent_type == 'user' and duel.player_two_id:
        from ratings.services import calculate_elo_change
        winner_is_first = duel.winner_id == duel.player_one_id
        if winner_is_first:
            rating_one, rating_two = calculate_elo_change(
                winner_rating=_get_rating_score(duel.player_one, duel.language),
                loser_rating=_get_rating_score(duel.player_two, duel.language),
                is_draw=duel.is_draw,
                winner_is_first=True,
            )
        else:
            rating_two, rating_one = calculate_elo_change(
                winner_rating=_get_rating_score(duel.player_two, duel.language),
                loser_rating=_get_rating_score(duel.player_one, duel.language),
                is_draw=duel.is_draw,
                winner_is_first=True,
            )

    result, _ = DuelResult.objects.update_or_create(
        duel=duel,
        defaults={
            'score_player_one': score_one,
            'score_player_two': score_two,
            'rating_change_player_one': rating_one,
            'rating_change_player_two': rating_two,
            'avg_time_player_one': avg_one,
            'avg_time_player_two': avg_two,
        },
    )
    return result


class CreateDuelSessionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Создать дуэль',
        description='Создание дуэли. Проходит через 3 стадии: language -> cefr_level -> mode.',
        request=CreateDuelSerializer,
        responses={201: DuelDetailSerializer},
    )
    def post(self, request):
        serializer = CreateDuelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        mode = data['mode']

        if mode == 'rated' and not _has_active_pro(request.user):
            return Response(
                {'detail': 'Рейтинговые дуэли доступны только для Pro подписчиков.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        language, level, err = _resolve_language_and_level(data['language_code'], data['cefr_level'])
        if err:
            return Response({'detail': err}, status=status.HTTP_404_NOT_FOUND)

        waiting = Duel.objects.filter(
            status='waiting',
            mode=mode,
            language=language,
            cefr_level=level,
            opponent_type='user',
        ).exclude(player_one=request.user).first()

        if waiting:
            waiting.player_two = request.user
            waiting.status = 'in_progress'
            waiting.started_at = timezone.now()
            waiting.current_round = 1
            waiting.save()
            for i in range(1, waiting.total_rounds + 1):
                _build_round_for_duel(waiting, i)
            duel = waiting
        else:
            duel = Duel.objects.create(
                player_one=request.user,
                language=language,
                cefr_level=level,
                mode=mode,
                opponent_type='user',
                status='waiting',
            )

        return Response(
            DuelDetailSerializer(duel).data,
            status=status.HTTP_201_CREATED,
        )


class DuelDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Детали дуэли',
        description='Получение полной информации о дуэли с раундами.',
        responses={200: DuelDetailSerializer},
    )
    def get(self, request, duel_id):
        try:
            duel = Duel.objects.prefetch_related('rounds').get(id=duel_id)
        except Duel.DoesNotExist:
            return Response({'detail': 'Дуэль не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id not in (duel.player_one_id, duel.player_two_id or None):
            return Response(
                {'detail': 'Вы не являетесь участником этой дуэли.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(DuelDetailSerializer(duel).data, status=status.HTTP_200_OK)


class DuelWithAIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Дуэль с AI',
        description='Создание и автоматическое завершение дуэли с AI-противником. Все раунды генерируются и отвечаются сразу.',
        request=CreateDuelSerializer,
        responses={200: {'type': 'object'}},
    )
    def post(self, request):
        serializer = CreateDuelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        language, level, err = _resolve_language_and_level(data['language_code'], data['cefr_level'])
        if err:
            return Response({'detail': err}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            duel = Duel.objects.create(
                player_one=request.user,
                language=language,
                cefr_level=level,
                mode='casual',
                opponent_type='ai',
                status='in_progress',
                started_at=timezone.now(),
                current_round=1,
            )
            for i in range(1, duel.total_rounds + 1):
                rnd = _build_round_for_duel(duel, i)
                ai_answer = AIService().ai_duel_answer(
                    user=request.user,
                    question=rnd.question_text,
                    options=rnd.options,
                    level_code=duel.cefr_level.level,
                )
                rnd.answer_player_two = ai_answer
                rnd.time_player_two = float(len(ai_answer) * 0.3 + 1)
                rnd.save()

        result = _finalize_duel(duel)
        duel.refresh_from_db()

        return Response(
            {
                'detail': 'Дуэль с AI завершена.',
                'duel': DuelDetailSerializer(duel).data,
                'result': {
                    'score_player_one': result.score_player_one,
                    'score_player_two': result.score_player_two,
                    'winner': duel.winner.username if duel.winner else None,
                    'is_draw': duel.is_draw,
                },
            },
            status=status.HTTP_200_OK,
        )


class DuelHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='История дуэлей',
        description='Список завершённых дуэлей текущего пользователя.',
        responses={200: DuelListSerializer(many=True)},
    )
    def get(self, request):
        duels = (
            Duel.objects.filter(status='finished')
            .filter(Q(player_one=request.user) | Q(player_two=request.user))
            .select_related('language', 'cefr_level', 'player_one', 'player_two', 'result')
        )

        serializer = DuelListSerializer(duels, many=True, context={'user': request.user})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DuelResultView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Результат дуэли',
        description='Детальный результат дуэли со статистикой и рекомендациями.',
        responses={200: DuelResultWithRecommendationSerializer},
    )
    def get(self, request, duel_id):
        try:
            duel = Duel.objects.prefetch_related('rounds').get(id=duel_id)
        except Duel.DoesNotExist:
            return Response({'detail': 'Дуэль не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id not in (duel.player_one_id, duel.player_two_id or None):
            return Response(
                {'detail': 'Вы не являетесь участником этой дуэли.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        result = getattr(duel, 'result', None)
        if duel.status != 'finished' and not result:
            result = _finalize_duel(duel)
            duel.refresh_from_db()

        serializer = DuelResultWithRecommendationSerializer(result, context={'user': request.user})
        return Response(serializer.data, status=status.HTTP_200_OK)
