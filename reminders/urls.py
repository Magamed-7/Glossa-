from django.urls import path
from .views import ReminderScheduleView

app_name = 'reminders'

urlpatterns = [
    path('schedule/', ReminderScheduleView.as_view(), name='reminder-schedule'),
]