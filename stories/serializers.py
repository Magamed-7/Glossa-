from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Story, StoryWord, UserStoryProgress

User = get_user_model()


class StoryWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryWord
        fields = [
            'id',
            'word',
            'translation',
            'part_of_speech',
            'context_sentence',
            'difficulty',
            'audio_url',
            'note',
        ]


class StoryAuthorSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'avatar_url']

    def get_avatar_url(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile:
            return profile.avatar_url
        return ''


class StoryListSerializer(serializers.ModelSerializer):
    author = StoryAuthorSerializer(source='created_by', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    level = serializers.CharField(source='cefr_level.level', read_only=True)

    class Meta:
        model = Story
        fields = [
            'id',
            'title',
            'language_code',
            'language_name',
            'level',
            'topic',
            'tags',
            'source',
            'status',
            'is_featured',
            'is_premium',
            'read_time_minutes',
            'views_count',
            'author',
            'created_at',
        ]


class StoryDetailSerializer(serializers.ModelSerializer):
    author = StoryAuthorSerializer(source='created_by', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    level = serializers.CharField(source='cefr_level.level', read_only=True)
    words = StoryWordSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = [
            'id',
            'title',
            'content',
            'language_code',
            'language_name',
            'level',
            'topic',
            'tags',
            'source',
            'status',
            'is_featured',
            'is_premium',
            'read_time_minutes',
            'views_count',
            'words',
            'author',
            'created_at',
            'updated_at',
        ]


class StoryCreateSerializer(serializers.ModelSerializer):
    ALLOWED_LEVELS = ['B2', 'C1', 'C2']

    class Meta:
        model = Story
        fields = [
            'title',
            'content',
            'language',
            'cefr_level',
            'topic',
            'tags',
            'read_time_minutes',
        ]

    def validate_cefr_level(self, value):
        if value.level not in self.ALLOWED_LEVELS:
            raise serializers.ValidationError(
                f'Истории можно публиковать только с уровня B2 и выше. '
                f'Ваш выбранный уровень: {value.level}.'
            )
        return value

    def validate(self, data):
        language = data.get('language')
        cefr_level = data.get('cefr_level')
        if language and cefr_level and cefr_level.language != language:
            raise serializers.ValidationError(
                'Уровень CEFR должен относиться к выбранному языку.'
            )
        return data
