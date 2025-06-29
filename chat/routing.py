
from django.urls import re_path
from chat.consumers import ChatConsumer, GroupChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<friend_id>\d+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/group/(?P<group_id>\d+)/$", GroupChatConsumer.as_asgi()),
]
