from django.urls import path
from .views import ExplainWordView, GenerateStoryView

app_name = 'ai'

urlpatterns = [
    path('explain-word/', ExplainWordView.as_view(), name='explain-word'),
    path('generate-story/', GenerateStoryView.as_view(), name='generate-story'),
]
