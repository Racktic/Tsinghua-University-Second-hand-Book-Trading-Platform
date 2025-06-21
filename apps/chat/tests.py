from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.sales.models import Item
from apps.chat.models import ChatRoom, Message
from apps.chat.utils import send_system_notification
from apps.chat.consumers import ChatConsumer
from channels.testing import WebsocketCommunicator

class ChatRoomTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.seller = User.objects.create_user(email="seller@example.com", username= "seller@example.com", password="password")
        self.buyer = User.objects.create_user(email="buyer@example.com", username= "buyer@example.com", password="password")
        # 创建测试物品
        self.item = Item.objects.create(
            title="Test Item",
            username=self.seller.email,
            price_lower_bound=10.00,
            price_upper_bound=20.00,
            user=self.seller,
            meta_info={"author": "张三慧", "course": "大学物理B", "teacher": "魏洋", "description": "这是魏洋老师的大物B的课本。本人几乎没有用，非常新。", "new": 0.99},
            picture="test_image.jpg",
        )
    def test_create_chat_room_invalid_item(self):
        """
        测试创建房间时物品不存在
        """
        # buyer登录
        self.client.login(email=self.buyer.email, password="password")
        response = self.client.post('/chat/create-room', {
            "item_id": 9999,  # 不存在的物品ID
            "buyer_email": self.buyer.email,
        }, format='json')
        print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('item_id', response.data)  # 检查是否包含 'item_id' 错误
        self.assertEqual(response.data['item_id'][0], "Item does not exist.")  # 检查具体错误信息
    
    def test_create_chat_room_success(self):
        """
        测试创建买家和卖家的共享房间
        """
        # buyer登录
        self.client.login(email=self.buyer.email, password="password")
        response = self.client.post('/chat/create-room', {
            "item_id": self.item.id,
            "buyer_email": self.buyer.email,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("room_name", response.data)
        self.assertTrue(ChatRoom.objects.filter(room_name=response.data["room_name"]).exists())
    def test_create_chat_room_existing_room(self):
        """
        测试创建房间时房间已存在
        """
        # buyer登录
        self.client.login(email=self.buyer.email, password="password")
        # 创建房间
        room, created = ChatRoom.objects.get_or_create(
            seller=self.seller,
            buyer=self.buyer,
            item=self.item,
            defaults={'room_name': f"room_{self.item.id}_{self.seller.id}_{self.buyer.id}"}
        )
        response = self.client.post('/chat/create-room', {
            "item_id": self.item.id,
            "buyer_email": self.buyer.email,
        }, format='json')
        print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["room_name"], room.room_name)
        self.assertFalse(response.data["created"])
    def test_create_chat_room_unlogged_buyer(self):
        """
        测试创建房间时买家不存在
        """
        # buyer未登录
        self.client.logout()
        response = self.client.post('/chat/create-room', {
            "item_id": self.item.id,
            "buyer_email": self.buyer.email,
        }, format='json')
        print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], "User is not logged in")  # 检查具体错误信息
    
    def test_create_chat_room_invalid_format(self):
        """
        测试创建房间时请求格式不正确
        """
        # buyer登录
        self.client.login(email=self.buyer.email, password="password")
        response = self.client.post('/chat/create-room', {
            "item_id": self.item.id,
        }, format='json')
        print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('buyer_email', response.data)  

    def test_get_existing_chat_room(self):
        """
        测试获取已存在的买家和卖家的共享房间
        """
        # buyer登录
        self.client.login(email=self.buyer.email, password="password")
        # 创建房间
        room, created = ChatRoom.objects.get_or_create(
            seller=self.seller,
            buyer=self.buyer,
            item =self.item,
            defaults={'room_name': f"room_{self.item.id}_{self.seller.id}_{self.buyer.id}"}
        )

        response = self.client.post('/chat/create-room', {
            "item_id": self.item.id,
            "buyer_email": self.buyer.email,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["room_name"], room.room_name)
        self.assertFalse(response.data["created"])  # 房间已存在


class SystemRoomTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(email="user@example.com", username= "user@example.com", password="password")

    def test_system_room_creation(self):
        """
        测试用户的系统房间是否正确创建
        """
        room = ChatRoom.objects.get(room_name=f"system_room_{self.user.id}")
        self.assertTrue(room.is_system_room)
        self.assertEqual(room.buyer, self.user)

    def test_send_system_notification(self):
        """
        测试系统通知的发送
        """
        message = "This is a test system notification."
        send_system_notification(self.user, message, 'chat_message')

        # 检查消息是否存储在系统房间
        room = ChatRoom.objects.get(room_name=f"system_room_{self.user.id}")
        messages = Message.objects.get(room=room)
        self.assertEqual(messages.room, room)
        self.assertEqual(messages.content, message)


class WebSocketTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.seller = User.objects.create_user(email="seller@example.com", username= "seller@example.com", password="password")
        self.buyer = User.objects.create_user(email="buyer@example.com", username= "buyer@example.com", password="password")
        self.item = Item.objects.create(
            title="Test Item",
            username=self.seller.email,
            price_lower_bound=10.00,
            price_upper_bound=20.00,
            user=self.seller
        )
        self.room, _ = ChatRoom.objects.get_or_create(
            seller=self.seller,
            buyer=self.buyer,
            defaults={'room_name': f"room_{self.item.id}_{self.seller.id}_{self.buyer.id}"}
        )
        Message.objects.create(room=self.room, sender=self.seller, content="Hello Buyer!")
        Message.objects.create(room=self.room, sender=self.buyer, content="Hello Seller!")
        print("seller_id:", self.seller.id)
        print("buyer_id:", self.buyer.id)

    async def test_buyer_seller_shared_room_websocket(self):

        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            path=f"/ws/chat/{self.item.id}/{self.buyer.email}/"
        )
        communicator.scope['url_route'] = {
            'kwargs': {
                'item_id': self.item.id,
                'buyer_email': self.buyer.email
            }
        }

        # Step 1: Connect to WebSocket
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Step 2: Handle Initial History Response
        history_response = await communicator.receive_json_from()
        print("Received history response:", history_response)
        self.assertEqual(history_response['type'], 'history')
        self.assertEqual(len(history_response['messages']), 2)
        self.assertEqual(history_response['messages'][0]['content'], "Hello Buyer!")
        self.assertEqual(history_response['messages'][1]['content'], "Hello Seller!")

        # Step 3: Send a Message
        message = "Hello from Buyer!"
        await communicator.send_json_to({
            'message': message,
            'sender_id': self.buyer.id
        })

        # Step 4: Receive the Sent Message
        chat_response = await communicator.receive_json_from()
        print("Received chat response:", chat_response)
        self.assertEqual(chat_response['type'], 'message')
        self.assertEqual(chat_response['message'], message)

        # Step 5: Disconnect
        await communicator.disconnect()

    async def test_system_room_websocket(self):
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            path=f"/ws/chat/system/{self.seller.id}/"
        )
        communicator.scope['user'] = self.seller
        communicator.scope['url_route'] = {
            'kwargs': {
                'user_id': self.seller.id
            }
        }

        # Step 1: Connect to WebSocket
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Step 2: Handle Initial History Response
        history_response = await communicator.receive_json_from()
        print("Received system history response:", history_response)
        self.assertEqual(history_response['type'], 'history')
        self.assertEqual(len(history_response['messages']), 0)
        # Step 3: Send a System Notification
        message = "This is a test system notification."
        await communicator.send_json_to({
            'message': message,
            'sender_id': self.seller.id
        })
        # Step 4: Receive the Sent Message
        system_response = await communicator.receive_json_from()
        print("Received system response:", system_response)
        self.assertEqual(system_response['type'], 'message')
        self.assertEqual(system_response['message'], message)

class ChatHistoryTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(email="seller@example.com", username="seller@example.com", password="password")
        self.buyer = User.objects.create_user(email="buyer@example.com", username="buyer@example.com", password="password")
        self.item = Item.objects.create(
            title="Test Item",
            username=self.seller.email,
            price_lower_bound=10.00,
            price_upper_bound=20.00,
            user=self.seller,
            meta_info={"author": "张三慧", "course": "大学物理B", "teacher": "魏洋", "description": "这是魏", "new": 0.99},
            picture=None,
        )
        self.room, _ = ChatRoom.objects.get_or_create(
            seller=self.seller,
            buyer=self.buyer,
            defaults={'room_name': f"room_{self.item.id}_{self.seller.id}_{self.buyer.id}"}
        )
        # 创建历史消息
        Message.objects.create(room=self.room, sender=self.seller, content="Hello Buyer!")
        Message.objects.create(room=self.room, sender=self.buyer, content="Hello Seller!")

    async def test_load_chat_history(self):
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            path=f"/ws/chat/{self.item.id}/{self.buyer.email}/"
        )
        communicator.scope['url_route'] = {
            'kwargs': {
                'item_id': self.item.id,
                'buyer_email': self.buyer.email
            }
        }

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # 接收历史消息
        response = await communicator.receive_json_from()
        print("Received response:", response)
        self.assertEqual(response['type'], 'history')
        self.assertEqual(len(response['messages']), 2)
        self.assertEqual(response['messages'][0]['content'], "Hello Buyer!")
        self.assertEqual(response['messages'][1]['content'], "Hello Seller!")
        self.assertEqual(response['messages'][0]['sender_id'], self.seller.id)
        self.assertEqual(response['messages'][1]['sender_id'], self.buyer.id)

        await communicator.disconnect()

class ListChatRoomsTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.user1 = User.objects.create_user(email="user1@example.com", username="user1@example.com", password="password")
        self.user2 = User.objects.create_user(email="user2@example.com", username="user2@example.com", password="password1")
        self.user3 = User.objects.create_user(email="user3@example.com", username="user3@example.com", password="password2")
        self.user4 = User.objects.create_user(email="user4@example.com", username="user4@example.com", password="password3")
        # 创建两个房间，user1 分别作为卖家和买家参与房间
        self.room1, _ = ChatRoom.objects.get_or_create(
            seller=self.user1,
            buyer=self.user2,
            defaults={'room_name': f"room_{self.user1.id}_{self.user2.id}"}
        )
        self.room2, _ = ChatRoom.objects.get_or_create(
            seller=self.user3,
            buyer=self.user1,
            defaults={'room_name': f"room_{self.user3.id}_{self.user1.id}"}
        )
    
    def test_list_chat_rooms_for_user1(self):
        # user1 登录后请求其所有房间
        self.client.login(email="user1@example.com", password="password")
        response = self.client.get('/chat/check-rooms', {'email': 'user1@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rooms = response.data
        print("Response data:", rooms)
        # user1 参与了3个房间（2普通房间 + 1系统房间）
        self.assertEqual(len(rooms), 3)
        for room in rooms:
            self.assertIn('room_name', room)
            self.assertIn('is_system_room', room)
            # 如果是系统房间，则只检查 buyer 信息，并确保 seller 信息返回默认值
            if room['is_system_room']:
                self.assertIn('buyer_email', room)
                self.assertIn('buyer_id', room)
                self.assertEqual(room.get('seller_email', ""), "")
                self.assertIsNone(room.get('seller_id', None))
            else:
                self.assertIn('seller_email', room)
                self.assertIn('buyer_email', room)
                self.assertIn('seller_id', room)
                self.assertIn('buyer_id', room)

    def test_list_chat_rooms_for_user4(self):
        # user4 登录后请求其所有房间
        self.client.login(email="user4@example.com", password="password3")
        response = self.client.get('/chat/check-rooms', {'email': 'user4@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rooms = response.data
        print("Response data:", rooms)
        # user4 没有参与任何房间
        self.assertEqual(len(rooms), 1)
    def test_list_chat_rooms_for_unlogged_user(self):
        # 未登录用户请求其所有房间
        response = self.client.get('/chat/check-rooms', {'email': 'user4@example.com'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], "User is not logged in")
