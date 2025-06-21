import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from apps.chat.models import ChatRoom, Message
        from apps.accounts.models import User
        from apps.sales.models import Item
        # 判断是买家和卖家的房间还是系统房间
        # 检查是否有 url_route 参数
        url_route = self.scope.get('url_route', {}).get('kwargs', {})
        if 'item_id' in url_route and 'buyer_email' in url_route:
            # 买家和卖家的共享房间，增加 item_id
            self.item_id = int(url_route['item_id'])
            buyer_email = url_route['buyer_email']

            # 使用 sync_to_async 获取 seller_id 和 buyer_id
            try:
                item = await sync_to_async(Item.objects.get)(id=self.item_id)
                self.seller_id = await sync_to_async(lambda: item.user.id)()
                self.buyer = await sync_to_async(User.objects.get)(email=buyer_email)
                self.buyer_id = self.buyer.id
                self.room_group_name = f"room_{self.item_id}_{self.seller_id}_{self.buyer_id}"
            except Item.DoesNotExist:
                await self.close()
                return
            except User.DoesNotExist:
                await self.close()
                return
            # print(f"[DEBUG] Connecting to shared room: {self.room_group_name}")
        else:
            # 系统房间
            if 'user_id' in url_route:
                # 从 URL 中获取用户 ID
                self.user_id = url_route['user_id']
            else:
                # 如果没有 URL 参数，尝试从 scope 中获取
                self.user_id = self.scope.get('user', {}).id if hasattr(self.scope.get('user', {}), 'id') else None
                
            if not self.user_id:
                await self.close()
                return
            self.room_group_name = f"system_room_{self.user_id}"
            # print(f"[DEBUG] Connecting to system room: {self.room_group_name}")

        # 将用户加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # 加载历史聊天记录
        messages = await sync_to_async(list)(
            Message.objects.filter(room__room_name=self.room_group_name)
            .order_by('timestamp')
            .values('content', 'timestamp', 'sender_id')
        )
        # 将 datetime 转换为字符串
        for message in messages:
            message['timestamp'] = message['timestamp'].isoformat()

        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        # 从房间组移除用户
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        from apps.chat.models import ChatRoom, Message
        from apps.accounts.models import User
        from apps.sales.models import Item
        # 接收来自 WebSocket 的消息
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']
        # print(f"[DEBUG] Received message: {message} from sender_id: {sender_id}")
        # print(f"[DEBUG] Sender ID: {sender_id}")
        try:
            # 获取发送者
            # print(f"[DEBUG] Fetching sender with ID: {sender_id}")
            try:
                sender = await sync_to_async(User.objects.get)(id=sender_id)
            except User.DoesNotExist:
                # print(f"[ERROR] User with id {sender_id} does not exist")
                return

            # print(f"[DEBUG] Sender found: {sender.email}")

            # 获取房间
            # print(f"[DEBUG] Fetching room with name: {self.room_group_name}")
            room = await sync_to_async(ChatRoom.objects.get)(room_name=self.room_group_name)
            # print(f"[DEBUG] Room found: {room.room_name}")

            # 保存消息到数据库
            saved_message = await sync_to_async(Message.objects.create)(
                room=room,
                sender=sender,
                content=message
            )
            # print(f"[DEBUG] Message saved to database: {saved_message.content} in room: {room.room_name}")

            # 将消息发送到房间组
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': sender_id
                }
            )
        except Exception as e:
            print(f"[ERROR] Failed to process message: {e}")

    async def chat_message(self, event):
        # 接收来自房间组的消息
        message = event['message']
        sender_id = event.get('sender_id', None)
        # print(f"[DEBUG] Broadcasting message: {message} from sender_id: {sender_id} to WebSocket")
        # 将消息发送到 WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message,
            'sender_id': sender_id
        }))