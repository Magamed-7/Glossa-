from django.urls import path
from .views import (
    StoryListView,
    StoryDetailView,
    StoryCreateView,
    StoryAIAssistView,
)

app_name = 'stories'

urlpatterns = [
    
    path('', StoryListView.as_view(), name='story-list'),
    path('create/', StoryCreateView.as_view(), name='story-create'),

    path('<uuid:pk>/', StoryDetailView.as_view(), name='story-detail'),

    path('<uuid:pk>/ai-assist/', StoryAIAssistView.as_view(), name='story-ai-assist'),
]
