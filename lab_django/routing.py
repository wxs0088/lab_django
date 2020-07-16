from django.urls import re_path,path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator

from lab_django.consumers import ChatConsumer,PushMessage,WebsshConsumer
application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                [
                    re_path(r"ws/(?P<room_name>\w+)/$", ChatConsumer),
                    path("ws/<room_name>", PushMessage),
                    path("web/", WebsshConsumer),
                ]
            )
        )
    )
})