from django.urls import path
from .views import (
    LessonListView,
    LessonDetailView,
    LessonTestSubmitView,
    GrammarBookmarkListView,
    GrammarBookmarkDeleteView,
)

app_name = 'grammar'

urlpatterns = [
    path('lessons/', LessonListView.as_view(), name='lesson-list'),

    path('lessons/<uuid:pk>/', LessonDetailView.as_view(), name='lesson-detail'),

    path('lessons/<uuid:pk>/submit/', LessonTestSubmitView.as_view(), name='lesson-submit'),

    path('bookmarks/', GrammarBookmarkListView.as_view(), name='bookmark-list'),

    path('bookmarks/<uuid:pk>/', GrammarBookmarkDeleteView.as_view(), name='bookmark-delete'),
]
