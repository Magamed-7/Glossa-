from django.urls import path
from .views import (
    DeckListView,
    AddWordView,
    ReviewSessionView,
    SubmitReviewView,
    MasteredWordsListView,
    RestartWordView,
)

app_name = 'learning'

urlpatterns = [
    path('deck/', DeckListView.as_view(), name='deck-list'),
    path('deck/add/', AddWordView.as_view(), name='deck-add'),

    path('review/', ReviewSessionView.as_view(), name='review-session'),

    path('review/<uuid:pk>/submit/', SubmitReviewView.as_view(), name='review-submit'),

    path('mastered/', MasteredWordsListView.as_view(), name='mastered-list'),

    path('mastered/<uuid:pk>/restart/', RestartWordView.as_view(), name='mastered-restart'),
]
