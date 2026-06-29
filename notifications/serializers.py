from rest_framework import serializers
from .models import Notification, PushSubscription


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'body',
            'is_read',
            'read_at',
            'channel',
            'duel',
            'story',
            'achievement',
            'created_at',
        ]
        read_only_fields = ['id', 'notification_type', 'title', 'body', 'channel', 'duel', 'story', 'achievement', 'created_at']


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ['id', 'endpoint', 'p256dh_key', 'auth_key', 'is_active', 'user_agent', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MarkReadSerializer(serializers.Serializer):
    notification_id = serializers.UUIDField()