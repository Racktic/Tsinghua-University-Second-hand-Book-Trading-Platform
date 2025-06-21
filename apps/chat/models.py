from django.db import models
from django.conf import settings


class ChatRoom(models.Model):
    """
    用于存储聊天房间信息
    """
    seller = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='chatrooms_seller', null=True, blank=True
    )
    buyer = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='chatrooms_buyer', null=True, blank=True
    )
    item = models.ForeignKey(
        'sales.Item', on_delete=models.CASCADE, related_name='chatrooms', null=True, blank=True
    )
    room_name = models.CharField(max_length=255, unique=True)  # 房间号，唯一
    is_system_room = models.BooleanField(default=False)  # 是否为系统房间
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.is_system_room:
            return f"System Room: {self.room_name}"
        return f"Room: {self.room_name} ({self.seller.email if self.seller else 'N/A'} - {self.buyer.email if self.buyer else 'N/A'})"


class Message(models.Model):
    """
    用于存储聊天记录
    """
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.email} in {self.room.room_name}"