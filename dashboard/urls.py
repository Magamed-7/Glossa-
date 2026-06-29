from django.urls import path
from .views import (
    OverviewView,
    UserManagementView,
    AnalyticsView,
    AILogsView,
)

app_name = 'dashboard'

urlpatterns = [
    path('overview/', OverviewView.as_view(), name='overview'),
    path('users/', UserManagementView.as_view(), name='user-management'),
    path('users/<uuid:pk>/ban/', UserManagementView.as_view(), name='user-ban'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('ai/', AILogsView.as_view(), name='ai-logs'),
]