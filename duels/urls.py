from django.urls import path
from .views import (
    CreateDuelSessionView,
    DuelDetailView,
    DuelWithAIView,
    DuelHistoryView,
    DuelResultView,
)

app_name = 'duels'

urlpatterns = [
    path('create/', CreateDuelSessionView.as_view(), name='create'),
    path('ai/', DuelWithAIView.as_view(), name='duel-with-ai'),
    path('history/', DuelHistoryView.as_view(), name='history'),
    path('<uuid:duel_id>/', DuelDetailView.as_view(), name='detail'),
    path('<uuid:duel_id>/result/', DuelResultView.as_view(), name='result'),
]
