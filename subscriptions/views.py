import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Plan, Subscription, PaymentEvent, TrialPeriod, PaymentRequest
from .serializers import (
    PlanSerializer,
    SubscriptionSerializer,
    PaymentCreateSerializer,
    PaymentEventSerializer,
    TrialPeriodSerializer,
    DemoPaySerializer,
    PaymentRequestCreateSerializer,
    PaymentRequestSerializer,
)

logger = logging.getLogger('subscriptions')

TRIAL_DURATION_DAYS = 4



class PlanListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Список тарифных планов',
        description='Все активные тарифные планы.',
        responses={200: PlanSerializer(many=True)},
    )
    def get(self, request):
        plans = Plan.objects.filter(is_active=True)
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Моя подписка',
        description='Текущая подписка, триал и история платежей.',
        responses={200: {'type': 'object'}},
    )
    def get(self, request):
        subscription = (
            Subscription.objects
            .filter(user=request.user, status='active')
            .select_related('plan')
            .order_by('-created_at')
            .first()
        )

        
        trial = getattr(request.user, 'trial_period', None)

        
        if subscription:
            payments = PaymentEvent.objects.filter(
                subscription__user=request.user
            ).order_by('-created_at')[:10]
        else:
            payments = []

        return Response(
            {
                'subscription': SubscriptionSerializer(subscription).data if subscription else None,
                'trial': TrialPeriodSerializer(trial).data if trial else None,
                'payments': PaymentEventSerializer(payments, many=True).data,
            },
            status=status.HTTP_200_OK,
        )



class CreatePaymentView(APIView):
    # 4. TODO
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Создать платёж',
        description='Создание платежа в статусе pending. Ожидается подтверждение.',
        request=PaymentCreateSerializer,
        responses={201: {'type': 'object'}},
    )
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        plan = Plan.objects.get(id=serializer.validated_data['plan_id'])
        method = serializer.validated_data['method']

        
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='pending',
        )

        
        payment = PaymentEvent.objects.create(
            subscription=subscription,
            method=method,
            amount=plan.price,
            currency=plan.currency,
            status='pending',
            is_demo=False,
        )

        logger.info(
            f'Создан платёж: {request.user.email} -> план {plan.name}, '
            f'метод {method}, сумма {plan.price} {plan.currency}'
        )

        return Response(
            {
                'detail': 'Платёж создан. Ожидается подтверждение.',
                'subscription_id': str(subscription.id),
                'payment': PaymentEventSerializer(payment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class DemoPayView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Демо-оплата',
        description='Эмуляция успешной оплаты. Только для DEBUG=True.',
        request=DemoPaySerializer,
        responses={201: {'type': 'object'}},
    )
    def post(self, request):
        if not getattr(settings, 'DEBUG', False):
            return Response(
                {'detail': 'Демо-оплата недоступна в production режиме.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DemoPaySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        plan_id = serializer.validated_data['plan_id']
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({'detail': 'Тариф не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if plan.period == 'free':
            return Response(
                {'detail': 'Нельзя "оплатить" бесплатный тариф.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        period_map = {
            'monthly': timedelta(days=30),
            'semi_annual': timedelta(days=182),
            'annual': timedelta(days=365),
        }
        duration = period_map.get(plan.period, timedelta(days=30))
        now = timezone.now()

       
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='active',
            started_at=now,
            expires_at=now + duration,
        )

        
        PaymentEvent.objects.create(
            subscription=subscription,
            method='card',
            amount=plan.price,
            currency=plan.currency,
            status='success',
            is_demo=True,
        )

        logger.info(f'[DEMO] Подписка активирована: {request.user.email} -> {plan.name}')

        return Response(
            {
                'detail': f'Демо-оплата успешна. Подписка "{plan.name}" активирована.',
                'subscription': SubscriptionSerializer(subscription).data,
            },
            status=status.HTTP_201_CREATED,
        )



class TrialActivationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Активировать пробный период',
        description='Активация 14-дневного триала. Одноразово. Создаёт подписку на 14 дней.',
        responses={201: {'type': 'object'}},
    )
    def post(self, request):
        user = request.user

        if hasattr(user, 'trial_period'):
            return Response(
                {'detail': 'Пробный период уже был использован.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


        active_sub = Subscription.objects.filter(
            user=user, status='active'
        ).first()
        if active_sub and active_sub.is_active:
            return Response(
                {'detail': 'У вас уже есть активная подписка.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        try:
            pro_plan = Plan.objects.get(period='monthly', is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {'detail': 'Pro тариф временно недоступен.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        now = timezone.now()
        expires = now + timedelta(days=TRIAL_DURATION_DAYS)

   
        subscription = Subscription.objects.create(
            user=user,
            plan=pro_plan,
            status='active',
            is_trial=True,
            started_at=now,
            expires_at=expires,
        )

       
        trial = TrialPeriod.objects.create(
            user=user,
            subscription=subscription,
            started_at=now,
            expires_at=expires,
            is_used=True,
        )

        # TODO

        logger.info(f'Триал активирован: {user.email}, истекает {expires}')

        return Response(
            {
                'detail': f'Пробный период на {TRIAL_DURATION_DAYS} дня успешно активирован.',
                'trial': TrialPeriodSerializer(trial).data,
            },
            status=status.HTTP_201_CREATED,
        )


TELEGRAM_LINK = 'https://t.me/6080339142'


class CreatePaymentRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Запрос на оплату через Telegram',
        description='Создаёт запрос на оплату. Пользователь переходит в Telegram для оплаты.',
        request=PaymentRequestCreateSerializer,
        responses={201: PaymentRequestSerializer},
    )
    def post(self, request):
        serializer = PaymentRequestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        plan = Plan.objects.get(id=serializer.validated_data['plan_id'])

        existing = PaymentRequest.objects.filter(
            user=request.user, status='pending'
        ).first()
        if existing:
            return Response(
                {
                    'detail': 'У вас уже есть запрос на оплату. Дождитесь подтверждения.',
                    'payment_request_id': str(existing.id),
                    'telegram_link': TELEGRAM_LINK,
                },
                status=status.HTTP_409_CONFLICT,
            )

        pr = PaymentRequest.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            currency=plan.currency,
        )

        logger.info(f'Запрос на оплату создан: {request.user.email} -> {plan.name}')

        return Response(
            {
                'detail': 'Запрос создан. Перейдите в Telegram для оплаты.',
                'payment_request_id': str(pr.id),
                'telegram_link': TELEGRAM_LINK,
                'amount': str(pr.amount),
                'currency': pr.currency,
                'plan_name': plan.name,
            },
            status=status.HTTP_201_CREATED,
        )


class MyPaymentRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Мой запрос на оплату',
        description='Текущий запрос на оплату (pending или последний).',
        responses={200: PaymentRequestSerializer},
    )
    def get(self, request):
        pr = PaymentRequest.objects.filter(
            user=request.user
        ).order_by('-created_at').first()

        if not pr:
            return Response({'payment_request': None}, status=status.HTTP_200_OK)

        return Response(
            {
                'payment_request': PaymentRequestSerializer(pr).data,
                'telegram_link': TELEGRAM_LINK,
            },
            status=status.HTTP_200_OK,
        )
