from rest_framework import serializers
from .models import Plan, Subscription, PaymentEvent, TrialPeriod, PaymentRequest


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id',
            'name',
            'period',
            'price',
            'currency',
            'description',
            

            'stories_per_day',
            'phrases_per_day',
            'stories_per_week',
            

            'rated_duels_access',
            'global_leaderboard',
            'ai_access',
            'full_catalog_access',
            'ai_story_assist',
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)  

    class Meta:
        model = Subscription
        fields = [
            'id',
            'plan',
            'status',
            'is_trial',
            'is_active',
            'started_at',
            'expires_at',
            'auto_renew',
            'created_at',
        ]


class PaymentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentEvent
        fields = [
            'id',
            'method',
            'amount',
            'currency',
            'status',
            'is_demo',
            'provider_payment_id',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'is_demo', 'provider_payment_id', 'created_at']


class PaymentCreateSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    method = serializers.ChoiceField(choices=['card', 'bank_account'])

    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError('Тариф не найден или недоступен.')
        if plan.period == 'free':
            raise serializers.ValidationError('Нельзя оплатить бесплатный тариф.')
        return value


class TrialPeriodSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)  

    class Meta:
        model = TrialPeriod
        fields = [
            'id',
            'started_at',
            'expires_at',
            'is_used',
            'is_active',
            'created_at',
        ]


class DemoPaySerializer(serializers.Serializer):
    plan_id = serializers.UUIDField(help_text='UUID тарифного плана для демо-оплаты')

    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError('Тариф не найден или недоступен.')
        if plan.period == 'free':
            raise serializers.ValidationError('Нельзя "оплатить" бесплатный тариф.')
        return value


class PaymentRequestCreateSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()

    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError('Тариф не найден или недоступен.')
        if plan.period == 'free':
            raise serializers.ValidationError('Нельзя запросить оплату бесплатного тарифа.')
        return value


class PaymentRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = PaymentRequest
        fields = [
            'id',
            'user',
            'user_email',
            'plan',
            'plan_name',
            'amount',
            'currency',
            'status',
            'admin_note',
            'created_at',
            'confirmed_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'admin_note', 'created_at', 'confirmed_at']
