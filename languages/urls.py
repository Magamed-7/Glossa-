from django.urls import path
from .views import (
    LanguageListView,
    CEFRLevelListView,
    AdminLanguageToggleView,
)

app_name = 'languages'

urlpatterns = [
    path('', LanguageListView.as_view(), name='language-list'),

    path('<str:lang_code>/levels/', CEFRLevelListView.as_view(), name='cefr-levels'),

    path('<str:lang_code>/toggle/', AdminLanguageToggleView.as_view(), name='language-toggle'),
]
