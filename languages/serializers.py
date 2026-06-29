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
    class Meta:
        model = Language
        fields = ['id', 'name', 'native_name', 'code', 'flag_emoji']


class LanguageToggleRequestSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(
        required=False,
        help_text=(
            'Если не передано — текущий флаг is_active просто инвертируется. '
            'Если передано — устанавливается явно (True/False).'
        ),
    )