from rest_framework import serializers

from .models import Duel, DuelRound, DuelResult


class DuelRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuelRound
        fields = [
            'id', 'round_number', 'round_type', 'question_text',
            'options', 'correct_answer', 'answer_player_one', 'answer_player_two',
            'time_player_one', 'time_player_two', 'round_winner', 'is_draw',
            'started_at', 'finished_at',
        ]
        read_only_fields = fields


class DuelResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuelResult
        fields = [
            'score_player_one', 'score_player_two',
            'rating_change_player_one', 'rating_change_player_two',
            'avg_time_player_one', 'avg_time_player_two',
        ]
        read_only_fields = fields


class DuelDetailSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)
    cefr_level = serializers.CharField(source='cefr_level.level', read_only=True)
    player_one_username = serializers.CharField(source='player_one.username', read_only=True)
    player_two_username = serializers.SerializerMethodField()
    winner_username = serializers.SerializerMethodField()
    rounds = DuelRoundSerializer(many=True, read_only=True)

    class Meta:
        model = Duel
        fields = [
            'id', 'player_one_username', 'player_two_username', 'winner_username',
            'language_code', 'cefr_level', 'mode', 'opponent_type', 'status',
            'total_rounds', 'current_round', 'time_per_round_seconds',
            'winner', 'is_draw', 'started_at', 'finished_at', 'created_at', 'rounds',
        ]
        read_only_fields = fields

    def get_player_two_username(self, obj):
        if obj.player_two:
            return obj.player_two.username
        return 'AI Тренер' if obj.opponent_type == 'ai' else None

    def get_winner_username(self, obj):
        if obj.winner:
            return obj.winner.username
        if obj.is_draw:
            return 'Ничья'
        return None


class DuelListSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)
    cefr_level = serializers.CharField(source='cefr_level.level', read_only=True)
    opponent_username = serializers.SerializerMethodField()
    result_score = serializers.SerializerMethodField()

    class Meta:
        model = Duel
        fields = [
            'id', 'mode', 'opponent_type', 'status', 'language_code', 'cefr_level',
            'opponent_username', 'result_score', 'is_draw', 'created_at', 'finished_at',
        ]
        read_only_fields = fields

    def _get_opponent(self, obj, user):
        if obj.player_one_id == user.id:
            return obj.player_two
        return obj.player_one

    def get_opponent_username(self, obj):
        user = self.context.get('user')
        if not user:
            return None
        opponent = self._get_opponent(obj, user)
        if opponent:
            return opponent.username
        return 'AI Тренер' if obj.opponent_type == 'ai' else None

    def get_result_score(self, obj):
        result = getattr(obj, 'result', None)
        if not result:
            return None
        return {
            'player_one': result.score_player_one,
            'player_two': result.score_player_two,
        }


class CreateDuelSerializer(serializers.Serializer):
    language_code = serializers.CharField(max_length=10)
    cefr_level = serializers.CharField(max_length=2)
    mode = serializers.ChoiceField(choices=['casual', 'rated'], default='casual')


class DuelResultWithRecommendationSerializer(serializers.ModelSerializer):
    duel = DuelDetailSerializer(read_only=True)
    recommended_words = serializers.SerializerMethodField()

    class Meta:
        model = DuelResult
        fields = [
            'duel', 'score_player_one', 'score_player_two',
            'rating_change_player_one', 'rating_change_player_two',
            'avg_time_player_one', 'avg_time_player_two', 'recommended_words',
        ]
        read_only_fields = fields

    def get_recommended_words(self, obj):
        user = self.context.get('user')
        if not user:
            return []
        wrong_rounds = obj.duel.rounds.filter(
            round_winner__isnull=True,
            is_draw=False,
        )
        words = []
        seen = set()
        for rnd in wrong_rounds:
            answer = (
                rnd.answer_player_one if obj.duel.player_one_id == user.id
                else rnd.answer_player_two
            )
            if answer and answer.lower() != rnd.correct_answer.lower() and rnd.correct_answer not in seen:
                words.append({
                    'word': rnd.correct_answer,
                    'context': rnd.question_text,
                    'options': rnd.options,
                })
                seen.add(rnd.correct_answer)
        return words
