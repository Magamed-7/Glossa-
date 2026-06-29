from rest_framework import serializers
from .models import Reminder, ReminderSchedule


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = [
            'id',
            'reminder_type',
            'title',
            'body',
            'status',
            'channel',
            'scheduled_at',
            'sent_at',
            'error_message',
            'created_at',
        ]
        read_only_fields = fields


class ReminderScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderSchedule
        fields = [
            'id',
            'is_enabled',
            'frequency',
            'preferred_time',
            'timezone',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']