from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # 买家和卖家的共享房间
    path('ws/chat/<int:item_id>/<str:buyer_email>/', consumers.ChatConsumer.as_asgi()),

    # 用户的系统房间
    path('ws/chat/system/<int:user_id>/', consumers.ChatConsumer.as_asgi()),
]