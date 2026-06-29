import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Achievement, UserAchievement
from .serializers import AchievementSerializer, UserAchievementSerializer

logger = logging.getLogger('achievements')


@extend_schema(
    responses={200: AchievementSerializer(many=True)},
    summary='Все доступные достижения',
    tags=['achievements'],
)
class AchievementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        achievements = Achievement.objects.all()
        serializer = AchievementSerializer(achievements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: UserAchievementSerializer(many=True)},
    summary='Полученные достижения текущего пользователя',
    tags=['achievements'],
)
class UserAchievementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
        serializer = UserAchievementSerializer(user_achievements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)