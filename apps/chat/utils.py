from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_system_notification(user, message, message_type):
    """
    向用户的系统房间发送系统通知，并保存到数据库
    """
    from apps.chat.models import ChatRoom, Message
    channel_layer = get_channel_layer()
    room_name = f"system_room_{user.id}"  # 用户的系统房间名
    print(f"[DEBUG] Sending system notification to room: {room_name}, message: {message}")
    # 确保房间存在
    room, created = ChatRoom.objects.get_or_create(
        room_name=room_name,
        is_system_room=True,
        buyer=user
    )
    # 如果是新创建的房间，确保设置了系统房间标志
    if created:
        print(f"[DEBUG] Created new system room for user: {user.email}")
    
    # 保存消息到数据库
    Message.objects.create(
        room=room,
        sender=user,  # 系统消息可以用用户自己作为发送者
        content=message
    )

    # 通过 WebSocket 发送消息
    async_to_sync(channel_layer.group_send)(
        room_name,  # 房间组名
        {
            'type': message_type,  # 消息类型
            'message': message,      # 消息内容
            'sender_id': user.id  
        }
    )