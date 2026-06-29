from rest_framework import serializers
from .models import Achievement, UserAchievement


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = [
            'id',
            'code',
            'title',
            'description',
            'icon',
            'category',
            'condition',
            'created_at',
        ]
        read_only_fields = fields


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = [
            'id',
            'achievement',
            'earned_at',
        ]
        read_only_fields = fields


class AchievementProgressSerializer(serializers.Serializer):
    achievement = AchievementSerializer()
    is_earned = serializers.BooleanField()
    progress = serializers.IntegerField(help_text='Прогресс выполнения (0-100 или текущее значение)')
    target = serializers.IntegerField(help_text='Целевое значение для достижения')