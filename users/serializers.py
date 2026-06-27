from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, EmailVerification, Friendship, UserLanguage

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            phone=validated_data.get('phone', '')
        )
        return user


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class UserLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLanguage
        fields = ['id', 'language_code', 'level', 'show_level', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['full_name', 'avatar_url', 'bio', 'native_language', 'timezone', 'ui_language', 'telegram_chat_id', 'updated_at']
        read_only_fields = ['updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    user_languages = UserLanguageSerializer(many=True, read_only=True)
    
    duel_count = serializers.SerializerMethodField()
    win_count = serializers.SerializerMethodField()
    achievements_count = serializers.SerializerMethodField()
    best_streak = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'is_verified', 'dashboard_role', 'push_enabled', 'push_token', 'profile', 'user_languages', 'duel_count', 'win_count', 'achievements_count', 'best_streak']
        read_only_fields = ['id', 'is_verified', 'dashboard_role']

    def get_duel_count(self, obj):
        if hasattr(obj, 'duels_as_player_one') and hasattr(obj, 'duels_as_player_two'):
            return obj.duels_as_player_one.count() + obj.duels_as_player_two.count()
        return 0

    def get_win_count(self, obj):
        if hasattr(obj, 'won_duels'):
            return obj.won_duels.count()
        return 0

    def get_achievements_count(self, obj):
        if hasattr(obj, 'user_achievements'):
            return obj.user_achievements.count()
        return 0

    def get_best_streak(self, obj):
        return 0


class FriendshipSerializer(serializers.ModelSerializer):
    from_user = serializers.SlugRelatedField(slug_field='username', read_only=True)
    to_user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class PublicAuthorProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    avatar_url = serializers.URLField(source='profile.avatar_url', read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)
    native_language = serializers.CharField(source='profile.native_language', read_only=True)
    user_languages = UserLanguageSerializer(many=True, read_only=True)
    
    duel_count = serializers.SerializerMethodField()
    win_count = serializers.SerializerMethodField()
    achievements_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar_url', 'bio', 'native_language', 'user_languages', 'duel_count', 'win_count', 'achievements_count']

    def get_duel_count(self, obj):
        if hasattr(obj, 'duels_as_player_one') and hasattr(obj, 'duels_as_player_two'):
            return obj.duels_as_player_one.count() + obj.duels_as_player_two.count()
        return 0

    def get_win_count(self, obj):
        if hasattr(obj, 'won_duels'):
            return obj.won_duels.count()
        return 0

    def get_achievements_count(self, obj):
        if hasattr(obj, 'user_achievements'):
            return obj.user_achievements.count()
        return 0
