from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    subscriptions_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'phone',
            'is_active',
            'is_verified',
            'dashboard_role',
            'push_enabled',
            'created_at',
            'last_login',
            'full_name',
            'subscriptions_count',
        ]
        read_only_fields = ['id', 'created_at', 'last_login']

    def get_full_name(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile and profile.full_name:
            return profile.full_name
        return ''

    def get_subscriptions_count(self, obj):
        if hasattr(obj, 'subscriptions'):
            return obj.subscriptions.count()
        return 0


class DashboardUserBanSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(help_text='True = разбанить, False = забанить')


class DashboardOverviewSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    pro_users = serializers.IntegerField()
    total_duels = serializers.IntegerField()
    total_stories = serializers.IntegerField()
    total_words_learned = serializers.IntegerField()


class DashboardAnalyticsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    new_users_this_week = serializers.IntegerField()
    active_users_this_week = serializers.IntegerField()
    free_vs_pro = serializers.DictField()
    total_duels = serializers.IntegerField()
    total_stories = serializers.IntegerField()
    total_lessons_completed = serializers.IntegerField()


class AILogSerializer(serializers.Serializer):
    total_requests = serializers.IntegerField()
    successful_requests = serializers.IntegerField()
    failed_requests = serializers.IntegerField()
    cached_requests = serializers.IntegerField()