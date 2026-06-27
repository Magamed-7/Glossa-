from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('users/', include('users.urls')),
    # path('grammars/', include('grammar.urls')),
    # path('ai/', include('ai.urls')),
    # path('duels/', include('duels.urls')),
    # path('languages/', include('languages.urls')),
    # path('learnings/', include('learning.urls')),
    # path('notifications/', include('notifications.urls')),
    # path('ratings/', include('ratings.urls')),
    # path('reminders/', include('reminders.urls')),
    # path('stories/', include('stories.urls')),
    # path('subscriptions/', include('subscriptions.urls')),
    # path('users/', include('dashboard .urls')),
    # path('subscriptions/', include('achievements .urls')),


    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]