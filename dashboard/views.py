import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse

from users.permissions import IsDashboardUser, IsSuperadmin, IsModerator, IsAnalyst
from .serializers import (
    DashboardUserSerializer,
    DashboardUserBanSerializer,
    DashboardOverviewSerializer,
    DashboardAnalyticsSerializer,
    AILogSerializer,
)

User = get_user_model()
logger = logging.getLogger('dashboard')


@extend_schema(
    responses={200: DashboardOverviewSerializer},
    summary='Обзор дашборда (superadmin/moderator/analyst)',
    tags=['dashboard'],
)
class OverviewView(APIView):
    permission_classes = [IsAuthenticated, IsDashboardUser]

    def get(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        pro_users = User.objects.filter(subscriptions__status='active').distinct().count()

        from duels.models import Duel
        total_duels = Duel.objects.count()

        from stories.models import Story
        total_stories = Story.objects.count()

        from learning.models import UserPhrase
        total_words_learned = UserPhrase.objects.values('user').distinct().count()

        data = {
            'total_users': total_users,
            'active_users': active_users,
            'pro_users': pro_users,
            'total_duels': total_duels,
            'total_stories': total_stories,
            'total_words_learned': total_words_learned,
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: DashboardUserSerializer(many=True)},
    summary='Управление пользователями (superadmin/moderator)',
    tags=['dashboard'],
)
class UserManagementView(APIView):
    permission_classes = [IsAuthenticated, IsModerator]

    def get(self, request):
        users = User.objects.select_related('profile').prefetch_related('subscriptions')
        role_param = request.query_params.get('role')
        if role_param:
            users = users.filter(dashboard_role=role_param)
        is_active_param = request.query_params.get('is_active')
        if is_active_param is not None:
            users = users.filter(is_active=is_active_param.lower() in ('true', '1'))
        search = request.query_params.get('search')
        if search:
            users = users.filter(username__icontains=search) | users.filter(email__icontains=search)
        users = users.order_by('-created_at')
        serializer = DashboardUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=DashboardUserBanSerializer,
        responses={
            200: OpenApiResponse(description='Пользователь забанен/разбанен'),
            404: OpenApiResponse(description='Пользователь не найден'),
        },
        summary='Забанить/разбанить пользователя (superadmin/moderator)',
        tags=['dashboard'],
    )
    def patch(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'detail': 'is_active обязателен.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = is_active
        user.save(update_fields=['is_active'])
        action = 'разблокирован' if is_active else 'заблокирован'
        logger.info(f'Пользователь {user.email} {action} модератором {request.user.email}')
        return Response({'detail': f'Пользователь {action}.'}, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: DashboardAnalyticsSerializer},
    summary='Аналитика (superadmin/analyst)',
    tags=['dashboard'],
)
class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAnalyst]

    def get(self, request):
        from duels.models import Duel
        from stories.models import Story
        from grammar.models import UserGrammarProgress
        from subscriptions.models import Subscription

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        total_users = User.objects.count()
        new_users_this_week = User.objects.filter(created_at__gte=week_ago).count()
        active_users_this_week = User.objects.filter(last_login__gte=week_ago).count()

        pro_users = Subscription.objects.filter(status='active').values('user').distinct().count()
        free_users = total_users - pro_users

        total_duels = Duel.objects.count()
        total_stories = Story.objects.count()
        total_lessons = UserGrammarProgress.objects.filter(status='completed').count()

        data = {
            'total_users': total_users,
            'new_users_this_week': new_users_this_week,
            'active_users_this_week': active_users_this_week,
            'free_vs_pro': {
                'free': free_users,
                'pro': pro_users,
            },
            'total_duels': total_duels,
            'total_stories': total_stories,
            'total_lessons_completed': total_lessons,
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: AILogSerializer},
    summary='Логи AI запросов (superadmin/analyst)',
    tags=['dashboard'],
)
class AILogsView(APIView):
    permission_classes = [IsAuthenticated, IsDashboardUser]

    def get(self, request):
        from ai.models import AIRequestLog

        total = AIRequestLog.objects.count()
        successful = AIRequestLog.objects.filter(status='success').count()
        failed = AIRequestLog.objects.filter(status='failed').count()
        cached = AIRequestLog.objects.filter(status='cached').count()

        data = {
            'total_requests': total,
            'successful_requests': successful,
            'failed_requests': failed,
            'cached_requests': cached,
        }
        return Response(data, status=status.HTTP_200_OK)