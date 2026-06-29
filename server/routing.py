from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from duels.routing import websocket_urlpatterns as duel_patterns
from notifications.routing import websocket_urlpatterns as notification_patterns

websocket_urlpatterns = duel_patterns + notification_patterns