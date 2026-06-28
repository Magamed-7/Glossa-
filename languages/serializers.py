from rest_framework import serializers
from .models import Language, CEFRLevel


class CEFRLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CEFRLevel
        fields = [
            'id',
            'level',
            'title',
            'description',
            'min_vocabulary',
            'max_vocabulary',
            'order',
        ]


class LanguageSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор языка.
    cefr_levels — вложенный список уровней, доступных для данного языка.
    """
    cefr_levels = CEFRLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Language
        fields = [
            'id',
            'name',
            'native_name',
            'code',
            'flag_emoji',
            'description',
            'is_active',
            'story_submission_min_level',
            'cefr_levels',
        ]


class LanguageShortSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор — используется в других app (stories, duels, learning и т.д.)
    без вложенного списка уровней, чтобы не нагружать ответ лишними данными.
    """
    class Meta:
        model = Language
        fields = ['id', 'name', 'native_name', 'code', 'flag_emoji']
