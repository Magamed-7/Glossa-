from django.urls import path
from .views import (
    NotificationListView,
    MarkReadView,
    RegisterPushTokenView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<uuid:notification_id>/read/', MarkReadView.as_view(), name='mark-read'),
    path('push-token/', RegisterPushTokenView.as_view(), name='push-token'),
]