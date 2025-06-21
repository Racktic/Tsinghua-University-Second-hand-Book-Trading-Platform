from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import User
from apps.sales.models import Item, Purchase
from django.utils import timezone
from datetime import timedelta

class PurchaseAPITests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.seller = User.objects.create_user(
            email="seller@test.com",
            username= "seller@test.com",
            password="testpassword123",
        )
        self.buyer = User.objects.create_user(
            email="buyer@test.com",
            username="buyer@test.com",
            password="testpassword123",

        )
        # 创建测试商品
        self.item = Item.objects.create(
            title="测试教材",
            username=self.seller.email,
            price_lower_bound=50.00,
            price_upper_bound=80.00,
            user=self.seller,
            meta_info={
                "author": "测试作者",
                "course": "测试课程",
                "teacher": "测试老师",
                "description": "这是一个测试描述",
                "new": 0.9
            }
        )
        
        # 设置URLs
        self.update_purchase_url = reverse('update-purchase')
        self.load_purchase_url = reverse('load-purchase')
        self.confirm_purchase_url = reverse('confirm-purchase')
        
    def tearDown(self):
        # 清理测试数据
        User.objects.all().delete()
        Item.objects.all().delete()
        Purchase.objects.all().delete()
    
    # UpdatePurchase 测试用例
    def test_update_purchase_create_new(self):
        """测试创建一个新的购买请求"""
        print("---------------------------------------------")
        print("test_update_purchase_create_new")
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        data = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "raiser_id": self.buyer.id,  # 买家发起请求
            "price": 60.00,
            "place": "一教",
            "time": "星期五第2节"
        }
        print("seller_id:", self.seller.id)
        print("item_user_id:", self.item.user.id)
        response = self.client.post(self.update_purchase_url, data, format='json')
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Purchase updated successfully")
        
        # 验证数据库中已创建购买请求
        self.assertTrue(Purchase.objects.filter(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer
        ).exists())
        print()
    
    def test_update_purchase_modify_existing(self):
        """测试修改已存在的购买请求"""
        print("---------------------------------------------")
        print("test_update_purchase_modify_existing")
        # 先创建一个购买请求
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期四第1节",
            checked=True,
            checked_at=timezone.now(),
            results=2,  # 未处理
            buyer_checked=True,
            room_sold=False
        )
        
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        # 修改购买请求
        data = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "raiser_id": self.buyer.id,
            "price": 70.00,  # 修改价格
            "place": "六教",  # 修改地点
            "time": "星期四第1节"
        }
        
        response = self.client.post(self.update_purchase_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证购买请求已更新
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertEqual(updated_purchase.price, 70.00)
        self.assertEqual(updated_purchase.place, "六教")
        self.assertEqual(updated_purchase.time, "星期四第1节")
        print("updated_purchase:", updated_purchase)
        print("checked:", updated_purchase.checked)
        print("checked_at:", updated_purchase.checked_at)
        print("results:", updated_purchase.results)
        print("buyer_checked:", updated_purchase.buyer_checked)
        print("room_sold:", updated_purchase.room_sold)
        print()
    
    def test_update_purchase_unauthorized_modification(self):
        """测试未经授权的修改请求"""
        print("---------------------------------------------")
        print("test_update_purchase_unauthorized_modification")
        # 创建一个由另一个买家发起的购买请求
        other_buyer = User.objects.create_user(
            email="other_buyer@test.com",
            username="other_buyer@test.com",
            password="testpassword123"
        )
        
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=other_buyer,  # 另一个买家发起
            price=60.00,
            place="一教",
            time="星期五第2节",
        )
        
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        # 买家尝试修改不是自己发起的请求
        data = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "raiser_id": self.buyer.id,  # 当前买家尝试声明为发起者
            "price": 70.00,
            "place": "六教",
            "time": "星期五第2节"
        }
        
        response = self.client.post(self.update_purchase_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print()
    
    def test_update_purchase_item_not_found(self):
        """测试指定不存在的商品ID"""
        print("---------------------------------------------")
        print("test_update_purchase_item_not_found")
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        data = {
            "item_id": 9999,  # 不存在的商品ID
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "raiser_id": self.buyer.id,
            "price": 60.00,
            "place": "一教",
            "time": "星期五第2节"
        }
        
        response = self.client.post(self.update_purchase_url, data, format='json')
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Item does not exist.")
        print()
    
    # LoadPurchase 测试用例
    def test_load_purchase_by_buyer(self):
        """测试买家加载购买请求"""
        print("---------------------------------------------")
        print("test_load_purchase_by_buyer")
        # 创建购买请求
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节"
        )
        
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        # 买家查看
        params = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "checker_id": self.buyer.id  # 买家查看
        }
        
        response = self.client.get(self.load_purchase_url, params)
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print()
    def test_load_purchase_by_buyer_after_seller_agree(self):
        """测试买家加载购买请求（卖家已同意）"""
        print("---------------------------------------------")
        print("test_load_purchase_by_buyer_after_seller_agree")
        # 创建一个已读的购买请求
        current_time = timezone.now()
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at=current_time,
            room_sold=True,
            buyer_checked=True,
            results=1  # 卖家已接受
        )
        self.client.login(email=self.buyer.email, password="testpassword123")
        params = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "checker_id": self.buyer.id  # 买家查看
        }
        response = self.client.get(self.load_purchase_url, params)
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 验证已标记为已读
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertTrue(updated_purchase.checked)
        self.assertIsNotNone(updated_purchase.checked_at)
        self.assertEqual(updated_purchase.results, 1)  # 卖家已接受
        print()

    def test_load_purchase_by_buyer_after_seller_reject(self):
        """测试买家加载购买请求（卖家已拒绝）"""
        print("---------------------------------------------")
        print("test_load_purchase_by_buyer_after_seller_reject")
        # 创建一个已读的购买请求
        current_time = timezone.now()
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at=current_time,
            buyer_checked=True,
            results=2  # 卖家已拒绝
        )
        self.client.login(email=self.buyer.email, password="testpassword123")
        params = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "checker_id": self.buyer.id  # 买家查看
        }
        response = self.client.get(self.load_purchase_url, params)
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 验证已标记为已读
        

    def test_load_purchase_by_seller_first_time(self):
        """测试卖家首次加载购买请求（应标记为已读）"""
        print("---------------------------------------------")
        print("test_load_purchase_by_seller_first_time")
        # 创建购买请求
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,  # 买家发起
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=False  # 未读
        )
        
        self.client.login(email=self.seller.email, password="testpassword123")
        
        # 卖家查看
        params = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "checker_id": self.seller.id  # 卖家查看
        }
        
        response = self.client.get(self.load_purchase_url, params)
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证已标记为已读
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertTrue(updated_purchase.checked)
        self.assertIsNotNone(updated_purchase.checked_at)
        print()
    
    def test_load_purchase_by_seller_second_time(self):
        """测试卖家第二次加载购买请求（应标记为已读）"""
        print("---------------------------------------------")
        print("test_load_purchase_by_seller_second_time")
        # 创建一个已读的购买请求
        current_time = timezone.now()  # 当前时间
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at=current_time,
        )
        
        self.client.login(email=self.seller.email, password="testpassword123")
        
        params = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "checker_id": self.seller.id  # 卖家查看
        }
        
        response = self.client.get(self.load_purchase_url, params)
        print("response:", response.data)
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(updated_purchase.results, 0) 
        print()

    def test_load_purchase_after_timeout(self):
        """测试超时后加载购买请求（应标记为拒绝）"""
        print("---------------------------------------------")
        print("test_load_purchase_after_timeout")
        # 创建一个已读但超时的购买请求
        past_time = timezone.now() - timedelta(minutes=1)  # 1分钟前，超过30秒
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at=past_time
        )
        
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        params = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "checker_id": self.buyer.id
        }
        
        response = self.client.get(self.load_purchase_url, params)
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证已标记为拒绝
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertEqual(updated_purchase.results, 2)  # 2表示拒绝
        print()
    
    def test_load_purchase_not_found(self):
        """测试加载不存在的购买请求"""
        print("---------------------------------------------")
        print("test_load_purchase_not_found")
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        params = {
            "item_id": 9999,  # 不存在的商品
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "checker_id": self.buyer.id
        }
        
        response = self.client.get(self.load_purchase_url, params)
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print()
    
    # ConfirmPurchase 测试用例
    def test_confirm_purchase_accepted_within_time(self):
        """测试卖家在时间内确认购买请求"""
        print("---------------------------------------------")
        print("test_confirm_purchase_accepted_within_time")
        # 创建一个已读、未超时的购买请求
        current_time = timezone.now()  # 当前时间
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at=current_time,
            results=0  # 未处理
        )
        
        self.client.login(email=self.seller.email, password="testpassword123")
        
        data = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "responder_id": self.seller.id,
            "confirm": True  # 接受
        }
        
        response = self.client.post(self.confirm_purchase_url, data, format='json')
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证购买请求已被接受
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertTrue(updated_purchase.room_sold)
        self.assertEqual(updated_purchase.results, 1)  # 1表示接受
        ## 验证item的状态
        self.assertTrue(Item.objects.filter(id=self.item.id).exists())
        item = Item.objects.get(id=self.item.id)
        self.assertEqual(item.sold, True)
        
        print()
    
    def test_confirm_purchase_rejected(self):
        """测试卖家拒绝购买请求"""
        print("---------------------------------------------")
        print("test_confirm_purchase_rejected")
        # 创建一个已读、未超时的购买请求
        current_time = timezone.now()  # 当前时间
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at=current_time,
            results=0  # 未处理
        )
        
        self.client.login(email=self.seller.email, password="testpassword123")
        
        data = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "responder_id": self.seller.id,
            "confirm": False  # 拒绝
        }
        
        response = self.client.post(self.confirm_purchase_url, data, format='json')
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证购买请求已被拒绝
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertEqual(updated_purchase.results, 2)  # 2表示拒绝
        print()
    
    def test_confirm_purchase_timeout(self):
        """测试超时后确认购买请求（应自动拒绝）"""
        print("---------------------------------------------")
        print("test_confirm_purchase_timeout")
        # 创建一个已读但超时的购买请求
        past_time = timezone.now() - timedelta(minutes=1)  # 1分钟前，超过30秒
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at=past_time,
            results=0  # 未处理
        )
        
        self.client.login(email=self.seller.email, password="testpassword123")
        
        data = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "responder_id": self.seller.id,
            "confirm": True  # 尝试接受，但已超时
        }
        
        response = self.client.post(self.confirm_purchase_url, data, format='json')
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证购买请求已被自动拒绝
        updated_purchase = Purchase.objects.get(id=purchase.id)
        self.assertEqual(updated_purchase.results, 2)  # 2表示拒绝
        print()

    
    def test_confirm_purchase_item_not_found(self):
        """测试确认不存在的购买请求"""
        print("---------------------------------------------")
        print("test_confirm_purchase_item_not_found")
        self.client.login(email=self.seller.email, password="testpassword123")
        
        data = {
            "item_id": 9999,  # 不存在的商品
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "responder_id": self.seller.id,
            "confirm": True
        }
        
        response = self.client.post(self.confirm_purchase_url, data, format='json')
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print()
    
    def test_confirm_purchase_by_buyer(self):
        """测试买家尝试确认购买请求（应该失败）"""
        print("---------------------------------------------")
        print("test_confirm_purchase_by_buyer")
        # 创建购买请求
        current_time = timezone.now()  # 当前时间
        purchase = Purchase.objects.create(
            item_id=self.item.id,
            seller=self.seller,
            buyer=self.buyer,
            raiser=self.buyer,
            price=60.00,
            place="一教",
            time="星期五第2节",
            checked=True,
            checked_at= current_time,
        )
        
        self.client.login(email=self.buyer.email, password="testpassword123")
        
        data = {
            "item_id": self.item.id,
            "seller_id": self.seller.id,
            "buyer_id": self.buyer.id,
            "responder_id": self.buyer.id,  # 买家尝试确认
            "confirm": True
        }
        
        response = self.client.post(self.confirm_purchase_url, data, format='json')
        print("response:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证返回的错误信息
        self.assertIn("Responder must be the seller", str(response.data))
        print()