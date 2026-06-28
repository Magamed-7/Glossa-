from rest_framework import serializers
from .models import UserPhrase, ReviewSession


class ReviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewSession
        fields = [
            'id',
            'easiness_factor',
            'interval_days',
            'repetitions',
            'consecutive_correct',
            'next_review_at',
            'last_result',
            'last_reviewed_at',
        ]


class UserPhraseSerializer(serializers.ModelSerializer):
    review_session = serializers.SerializerMethodField()
    language_code = serializers.CharField(source='language.code', read_only=True)

    class Meta:
        model = UserPhrase
        fields = [
            'id',
            'language',
            'language_code',
            'word',
            'translation',
            'context_sentence',
            'note',
            'source',
            'category',
            'story_word',
            'grammar_lesson',
            'status',
            'review_session',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def get_review_session(self, obj):
        session = obj.review_sessions.first()
        if session:
            return ReviewSessionSerializer(session).data
        return None


class ReviewSubmitSerializer(serializers.Serializer):
    RESULT_QUALITY_MAP = {
        'again': 2,
        'hard': 3,
        'good': 4,
        'easy': 5,
    }
    result = serializers.ChoiceField(choices=['again', 'hard', 'good', 'easy'])
