from django.urls import path
from .views import (
    AchievementListView,
    UserAchievementsView,
)

app_name = 'achievements'

urlpatterns = [
    path('', AchievementListView.as_view(), name='achievement-list'),
    path('me/', UserAchievementsView.as_view(), name='my-achievements'),
]