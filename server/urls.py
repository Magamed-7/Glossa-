from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    
    path('api/users/', include('users.urls')),
    path('api/languages/', include('languages.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/stories/', include('stories.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/grammar/', include('grammar.urls')),
    path('api/ai/', include('ai.urls')),
    path('api/duels/', include('duels.urls')),
    # path('api/ratings/', include('ratings.urls')),
    # path('api/notifications/', include('notifications.urls')),
    # path('api/reminders/', include('reminders.urls')),
    # path('api/achievements/', include('achievements.urls')),
    # path('api/dashboard/', include('dashboard.urls')),

    # Swagger/Redoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
