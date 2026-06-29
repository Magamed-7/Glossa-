import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import ReminderSchedule
from .serializers import ReminderScheduleSerializer

logger = logging.getLogger('reminders')


@extend_schema(
    responses={200: ReminderScheduleSerializer},
    summary='Получить расписание напоминаний',
    tags=['reminders'],
)
class ReminderScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        schedule, created = ReminderSchedule.objects.get_or_create(user=request.user)
        serializer = ReminderScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ReminderScheduleSerializer,
        responses={
            200: ReminderScheduleSerializer,
            400: OpenApiResponse(description='Ошибка валидации'),
        },
        summary='Обновить расписание напоминаний',
        tags=['reminders'],
    )
    def patch(self, request):
        schedule, created = ReminderSchedule.objects.get_or_create(user=request.user)
        serializer = ReminderScheduleSerializer(schedule, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        logger.info(f'Расписание напоминаний обновлено для {request.user.email}')
        return Response(serializer.data, status=status.HTTP_200_OK)