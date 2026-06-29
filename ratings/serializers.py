from rest_framework import serializers
from .models import PlayerRating, RatingHistory


class PlayerRatingSerializer(serializers.ModelSerializer):
    language_name = serializers.CharField(source='language.name', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    win_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = PlayerRating
        fields = [
            'id',
            'user',
            'language',
            'language_name',
            'language_code',
            'score',
            'wins',
            'losses',
            'draws',
            'total_duels',
            'win_streak',
            'best_streak',
            'win_rate',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'language', 'wins', 'losses', 'draws', 'total_duels', 'win_streak', 'best_streak', 'updated_at']


class RatingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RatingHistory
        fields = [
            'id',
            'score_before',
            'score_after',
            'change',
            'reason',
            'created_at',
        ]
        read_only_fields = fields


class WeeklyLeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    win_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = PlayerRating
        fields = [
            'id',
            'username',
            'language_code',
            'score',
            'total_duels',
            'wins',
            'losses',
            'draws',
            'win_rate',
            'win_streak',
            'best_streak',
        ]


class GlobalLeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    win_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = PlayerRating
        fields = [
            'id',
            'username',
            'language_code',
            'score',
            'total_duels',
            'wins',
            'losses',
            'draws',
            'win_rate',
            'win_streak',
            'best_streak',
        ]