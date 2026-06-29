from django.urls import path
from .views import (
    WeeklyLeaderboardView,
    GlobalLeaderboardView,
    PlayerRatingView,
    RatingHistoryView,
)

app_name = 'ratings'

urlpatterns = [
    path('<str:lang_code>/weekly/', WeeklyLeaderboardView.as_view(), name='weekly-leaderboard'),
    path('<str:lang_code>/global/', GlobalLeaderboardView.as_view(), name='global-leaderboard'),
    path('<str:lang_code>/me/', PlayerRatingView.as_view(), name='my-rating'),
    path('<str:lang_code>/history/', RatingHistoryView.as_view(), name='rating-history'),
]