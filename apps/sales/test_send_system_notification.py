# 在文件开头添加更多导入
from unittest.mock import patch, MagicMock
from apps.chat.models import ChatRoom, Message
from apps.sales.models import Need, Item
from apps.accounts.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

# 使用更全面的补丁方式
class ItemMatchingNeedTests(APITestCase):
    """测试上传/修改物品与需求匹配并发送通知的功能"""

    def setUp(self):
        # 创建测试用户
        self.seller = User.objects.create_user(
            email="seller@example.com", 
            username="seller@example.com", 
            password="password123"
        )
        self.buyer = User.objects.create_user(
            email="buyer@example.com", 
            username="buyer@example.com", 
            password="password123"
        )
        
        # 确保系统房间存在
        self.system_room, _ = ChatRoom.objects.get_or_create(
            room_name=f"system_room_{self.buyer.id}",
            is_system_room=True,
            buyer=self.buyer
        )
        
        # 创建一个需求
        self.need = Need.objects.create(
            title="微积分教材",
            username="buyer@example.com",
            price_lower_bound=10.00,
            price_upper_bound=30.00,
            user=self.buyer,
            meta_info={
                "author": "崔建莲",
                "course": "微积分",
                "teacher": "崔建莲",
                "description": "需要微积分教材",
            },
            is_fulfilled=False
        )
        
        # 设置URL
        self.upload_url = reverse('upload-items')
        self.modify_url = reverse('modify-items')
        
        # 登录卖家
        self.client.login(email="seller@example.com", password="password123")
        
        # 创建channel_layer模拟对象
        self.mock_channel_layer = MagicMock()
        self.mock_channel_layer.group_send = MagicMock()

    # 使用更全面的patch方式
    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_upload_item_match_need_notification(self, mock_async_to_sync, mock_get_channel_layer):
        """测试上传匹配需求的物品并发送通知"""
        # 设置mock对象的返回值
        mock_get_channel_layer.return_value = self.mock_channel_layer
        mock_async_to_sync.return_value = lambda func: func
        
        # 上传匹配需求的物品
        data = {
            "title": "微积分入门",
            "username": "seller@example.com",
            "price_lower_bound": 15.00,
            "price_upper_bound": 25.00,
            "picture": None,
            "meta_info": {
                "author": "崔建莲", 
                "course": "微积分基础", 
                "teacher": "崔建莲", 
                "description": "微积分教材，几乎全新", 
                "new": 9
            }
        }
        
        # 发送请求
        response = self.client.post(self.upload_url, data, format='json')
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Item uploaded successfully", response.data["message"])
        
        # 获取新上传的商品
        item = Item.objects.latest('id')
        
        # 检查是否向买家发送了消息
        messages = Message.objects.filter(room=self.system_room)
        self.assertTrue(messages.exists())
        
        # 验证消息内容 - 仅需验证关键词出现
        has_match_message = False
        for message in messages:
            content = message.content
            if '微积分' in content and ('匹配' in content or str(item.id) in content):
                has_match_message = True
                break
        
        self.assertTrue(has_match_message, "未找到包含匹配信息的消息")

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_modify_item_match_need_notification(self, mock_async_to_sync, mock_get_channel_layer):
        """测试修改物品后匹配需求并发送通知"""
        # 设置mock对象的返回值
        mock_get_channel_layer.return_value = self.mock_channel_layer
        mock_async_to_sync.return_value = lambda func: func
        
        # 创建一个原始物品 - 不匹配需求
        original_item = Item.objects.create(
            title="数学书籍",
            username="seller@example.com",
            price_lower_bound=15.00,
            price_upper_bound=25.00,
            picture= None,
            user=self.seller,
            meta_info={
                "author": "未知", 
                "course": "未知课程", 
                "teacher": "未知老师", 
                "description": "普通数学书", 
                "new": 8
            }
        )
        
        # 修改物品使其匹配需求
        data = {
            "id": original_item.id,
            "title": "微积分基础教程",
            "username": "seller@example.com",
            "price_lower_bound": "15.00",
            "price_upper_bound": "25.00",
            "picture": None,
            "meta_info": {
                "author": "崔建莲", 
                "course": "微积分", 
                "teacher": "崔建莲", 
                "description": "微积分教材，几乎全新", 
                "new": 9
            }
        }
        
        # 发送请求
        response = self.client.post(self.modify_url, data, format='json')
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Item modified successfully", response.data["message"])
        
        # 检查是否向买家发送了消息
        messages = Message.objects.filter(
            room=self.system_room, 
            content__contains="微积分"
        )
        self.assertTrue(messages.exists())

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_upload_item_no_matching_need(self, mock_async_to_sync, mock_get_channel_layer):
        """测试上传物品没有匹配需求时不发送通知"""
        # 设置mock对象的返回值
        mock_get_channel_layer.return_value = self.mock_channel_layer
        mock_async_to_sync.return_value = lambda func: func
        
        # 上传不匹配任何需求的物品
        data = {
            "title": "独特的非常规书籍",
            "username": "seller@example.com",
            "price_lower_bound": 100.00,
            "price_upper_bound": 200.00,
            "picture": None,
            "meta_info": {
                "author": "非常特殊的作者", 
                "course": "不存在的课程", 
                "teacher": "虚构的老师", 
                "description": "一本不会匹配任何需求的书", 
                "new": 10
            }
        }
        
        # 发送请求
        response = self.client.post(self.upload_url, data, format='json')
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Item uploaded successfully", response.data["message"])
        
        # 确认数据库中没有新增匹配消息
        initial_message_count = Message.objects.filter(room=self.system_room).count()
        self.assertEqual(initial_message_count, 0, "不应有匹配消息被创建")

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_system_notification_with_message_type(self, mock_async_to_sync, mock_get_channel_layer):
        """测试系统通知函数接受消息类型参数"""
        # 设置mock对象的返回值
        mock_get_channel_layer.return_value = self.mock_channel_layer
        mock_async_to_sync.return_value = lambda func: func
        
        from apps.chat.utils import send_system_notification
        
        # 调用函数
        send_system_notification(self.buyer, "测试消息", 'chat_message')
        
        # 验证消息是否被创建
        message = Message.objects.filter(
            room=self.system_room,
            content="测试消息"
        ).first()
        
        self.assertIsNotNone(message, "消息应被创建")

class NeedMatchingItemTests(APITestCase):
    """测试上传/修改需求与商品匹配并发送通知的功能"""

    def setUp(self):
        # 创建测试用户
        self.seller = User.objects.create_user(
            email="seller@example.com", 
            username="seller@example.com", 
            password="password123"
        )
        self.buyer = User.objects.create_user(
            email="buyer@example.com", 
            username="buyer@example.com", 
            password="password123"
        )
        
        # 确保系统房间存在 - 买家系统房间
        self.buyer_system_room, _ = ChatRoom.objects.get_or_create(
            room_name=f"system_room_{self.buyer.id}",
            is_system_room=True,
            buyer=self.buyer
        )
        
        # 确保系统房间存在 - 卖家系统房间
        self.seller_system_room, _ = ChatRoom.objects.get_or_create(
            room_name=f"system_room_{self.seller.id}",
            is_system_room=True,
            buyer=self.seller
        )
        
        # 创建一个已有商品
        self.item = Item.objects.create(
            title="微积分教材详解",
            username="seller@example.com",
            price_lower_bound=15.00,
            price_upper_bound=25.00,
            user=self.seller,
            picture=None,
            meta_info={
                "author": "崔建莲",
                "course": "微积分",
                "teacher": "崔建莲",
                "description": "微积分教材，几乎全新",
                "new": 9
            },
            sold=False
        )
        
        # 设置URL
        self.raise_need_url = reverse('raise-need')
        self.modify_need_url = reverse('modify-need')
        
        # 登录买家
        self.client.login(email="buyer@example.com", password="password123")
        
        # 创建channel_layer模拟对象
        self.mock_channel_layer = MagicMock()
        self.mock_channel_layer.group_send = MagicMock()

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_raise_need_match_item_notification(self, mock_async_to_sync, mock_get_channel_layer):
        """测试上传匹配商品的需求并发送通知"""
        # 设置mock对象的返回值
        mock_get_channel_layer.return_value = self.mock_channel_layer
        mock_async_to_sync.return_value = lambda func: func
        
        # 上传匹配已有商品的需求
        data = {
            "title": "微积分教材",
            "username": "buyer@example.com",
            "price_lower_bound": 10.00,
            "price_upper_bound": 30.00,
            "meta_info": {
                "author": "崔建莲", 
                "course": "微积分", 
                "teacher": "崔建莲", 
                "description": "需要一本微积分教材"
            }
        }
        
        # 发送请求
        response = self.client.post(self.raise_need_url, data, format='json')
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Need raised successfully", response.data["message"])
        
        # 获取新上传的需求
        need = Need.objects.latest('id')
        
        # 检查是否向买家发送了消息
        buyer_messages = Message.objects.filter(room=self.buyer_system_room)
        self.assertTrue(buyer_messages.exists())
        
        # 检查是否向卖家发送了消息
        seller_messages = Message.objects.filter(room=self.seller_system_room)
        self.assertTrue(seller_messages.exists())
        
        # 验证卖家收到的消息内容
        has_match_message = False
        for message in seller_messages:
            content = message.content
            if '微积分' in content and '匹配' in content:
                has_match_message = True
                break
        
        self.assertTrue(has_match_message, "未找到发送给卖家的包含匹配信息的消息")

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_modify_need_match_item_notification(self, mock_async_to_sync, mock_get_channel_layer):
        """测试修改需求后匹配商品并发送通知"""
        # 设置mock对象的返回值
        mock_get_channel_layer.return_value = self.mock_channel_layer
        mock_async_to_sync.return_value = lambda func: func
        
        # 创建一个原始需求 - 不匹配任何商品
        original_need = Need.objects.create(
            title="物理教材",
            username="buyer@example.com",
            price_lower_bound=10.00,
            price_upper_bound=20.00,
            user=self.buyer,
            meta_info={
                "author": "未知作者", 
                "course": "物理学", 
                "teacher": "未知教师", 
                "description": "需要物理教材"
            },
            is_fulfilled=False
        )
        
        # 修改需求使其匹配已有商品
        data = {
            "id": original_need.id,
            "title": "微积分教材",
            "username": "buyer@example.com",
            "price_lower_bound": 10.00,
            "price_upper_bound": 30.00,
            "meta_info": {
                "author": "崔建莲", 
                "course": "微积分", 
                "teacher": "崔建莲", 
                "description": "需要一本微积分教材"
            }
        }
        
        # 发送请求
        response = self.client.post(self.modify_need_url, data, format='json')
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Need modified successfully", response.data["message"])
        
        # 检查是否向买家发送了消息
        buyer_messages = Message.objects.filter(
            room=self.buyer_system_room, 
            content__contains="微积分"
        )
        self.assertTrue(buyer_messages.exists())
        
        # 检查是否向卖家发送了消息
        seller_messages = Message.objects.filter(
            room=self.seller_system_room, 
            content__contains="微积分"
        )
        self.assertTrue(seller_messages.exists())

    @patch('channels.layers.get_channel_layer')
    @patch('asgiref.sync.async_to_sync')
    def test_raise_need_no_matching_item(self, mock_async_to_sync, mock_get_channel_layer):
        """测试上传需求没有匹配商品时不发送通知"""
        # 设置mock对象的返回值
        mock_get_channel_layer.return_value = self.mock_channel_layer
        mock_async_to_sync.return_value = lambda func: func
        
        # 上传不匹配任何商品的需求
        data = {
            "title": "独特的非常规需求",
            "username": "buyer@example.com",
            "price_lower_bound": 5.00,
            "price_upper_bound": 15.00,
            "meta_info": {
                "author": "非常特殊的作者", 
                "course": "不存在的课程", 
                "teacher": "虚构的老师", 
                "description": "一本不会匹配任何商品的书"
            }
        }
        
        # 发送请求
        response = self.client.post(self.raise_need_url, data, format='json')
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Need raised successfully", response.data["message"])
        
        # 确认数据库中没有新增匹配消息
        initial_seller_message_count = Message.objects.filter(room=self.seller_system_room).count()
        self.assertEqual(initial_seller_message_count, 0, "不应有匹配消息被创建并发送给卖家")
        
        initial_buyer_message_count = Message.objects.filter(room=self.buyer_system_room).count()
        self.assertEqual(initial_buyer_message_count, 0, "不应有匹配消息被创建并发送给买家")
