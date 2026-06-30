from rest_framework import serializers
from .models import GrammarLesson, GrammarExample, GrammarQuestion, UserGrammarProgress, GrammarBookmark


class GrammarExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarExample
        fields = ['id', 'sentence', 'translation', 'explanation', 'is_from_story', 'story', 'order']


class GrammarQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarQuestion
        fields = ['id', 'question_type', 'question_text', 'options', 'explanation', 'order']


class GrammarLessonSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)
    level = serializers.CharField(source='cefr_level.level', read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    progress_status = serializers.SerializerMethodField()

    class Meta:
        model = GrammarLesson
        fields = [
            'id', 'title', 'language_code', 'level', 'explanation', 'tip',
            'is_premium', 'tags', 'order', 'read_time_minutes',
            'is_bookmarked', 'progress_status'
        ]

    def get_is_bookmarked(self, obj):
        user = self.context.get('request').user if 'request' in self.context else None
        if user and user.is_authenticated:
            return GrammarBookmark.objects.filter(user=user, lesson=obj).exists()
        return False

    def get_progress_status(self, obj):
        user = self.context.get('request').user if 'request' in self.context else None
        if user and user.is_authenticated:
            progress = UserGrammarProgress.objects.filter(user=user, lesson=obj).first()
            if progress:
                return progress.status
        return 'not_started'


class GrammarLessonDetailSerializer(GrammarLessonSerializer):
    examples = GrammarExampleSerializer(many=True, read_only=True)
    questions = GrammarQuestionSerializer(many=True, read_only=True)

    class Meta(GrammarLessonSerializer.Meta):
        fields = GrammarLessonSerializer.Meta.fields + ['examples', 'questions']


class UserGrammarProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGrammarProgress
        fields = ['id', 'status', 'score', 'max_score', 'attempts', 'completed_at', 'last_attempt_at']


class GrammarBookmarkSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = GrammarBookmark
        fields = ['id', 'lesson', 'lesson_title', 'created_at']
        read_only_fields = ['id', 'created_at']


class LessonTestSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.CharField(),
        help_text='Словарь {question_id: answer}, например {"uuid-question-id": "reads"}'
    )


class BookmarkCreateSerializer(serializers.Serializer):
    lesson = serializers.UUIDField(help_text='UUID урока для добавления в закладки')
