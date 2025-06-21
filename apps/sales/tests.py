from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import User
from apps.sales.models import Item, Need
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class UploadItemsTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.test_user_email = "testuser_upload@mails.tsinghua.edu.cn"
        self.test_user_password = "testpassword123"
        self.test_user = User.objects.create_user(
            email=self.test_user_email,
            username=self.test_user_email,
            password=self.test_user_password,
        )
        self.test_user2_email = "testuser2_upload@mails.tsinghua.edu.cn"
        self.test_user2_password = "testpassword2222"
        self.test_user2 = User.objects.create_user(
            email=self.test_user2_email,
            username=self.test_user2_email,
            password=self.test_user2_password,
        )
        # 创建测试物品
        self.item0 = Item.objects.create(
            title='数字逻辑与数字集成电路',
            username=self.test_user2_email,
            price_lower_bound=20.01,
            price_upper_bound=27.54,
            user=self.test_user2,
            meta_info={"author": "杨世强", "course": "数字逻辑电路", "teacher": "赵有键", "description": "本书为计算机系数字逻辑电路课程的教材", "new": 9},
            picture=None,
        )
        self.item1 = Item.objects.create(
            title="微积分教程",
            username=self.test_user_email,
            price_lower_bound=20,
            price_upper_bound=25.00,
            user=self.test_user,
            meta_info={"author": "崔建莲", "course": "微积分A", "teacher": "崔建莲", "description": "这是崔建莲老师的微积分A1课本。本人只在书上标注了一些作业题目，基本上没有破损和褶皱。", "new": 9},
            picture='item_pictures/test_image.jpg',  # 假设有一个测试图片
        )

        self.item2 = Item.objects.create(
            title="线性代数入门",
            username=self.test_user2_email,
            price_lower_bound=15.00,
            price_upper_bound=23.45,
            user=self.test_user2,
            meta_info={"author": "梁鑫", "course": "线性代数", "teacher": "史灵生", "description": "这是史灵生老师的线性代数课程的教材。本人在课本中画了一些重要知识点并且做了一些草稿，但是书本身没有破坏。", "new": 6},
            picture=None,
        )

        self.item3 = Item.objects.create(
            title="大学物理学",
            username=self.test_user_email,
            price_lower_bound=20.01,
            price_upper_bound=27.54,
            user=self.test_user,
            meta_info={"author": "张三慧", "course": "大学物理B", "teacher": "魏洋", "description": "这是魏洋老师的大物B的课本。本人几乎没有用，非常新。", "new": 9},
            picture=None,
        )

        self.item4 = Item.objects.create(
            title="微积分",
            username=self.test_user_email,
            price_lower_bound=15.00,
            price_upper_bound=23.45,
            user=self.test_user,
            meta_info={"author": "章纪民", "course": "微积分A", "teacher": "王振波", "description": "这是王振波老师的微积分A2课程的教材。本人在课本中画了一些重要知识点并且做了一些草稿，但是书本身没有破坏。", "new": 7},
            picture=None,
        )
        self.item5 = Item.objects.create(
            title = "tt",
            username = self.test_user2_email,
            price_lower_bound = 20.01,
            price_upper_bound = 27.54,
            user = self.test_user2,
            meta_info = {"author": "tt", "course": "tt", "teacher": "tt", "description": "tt", "new": 9},
            picture = None,
        )

        self.search_url = reverse('search-items')  
        self.upload_url = reverse('upload-items') 
        self.raise_need_url = reverse("raise-need")

    def tearDown(self):
        # 确保每次测试后用户登出
        self.client.logout()
        print("Tear down: User logged out.")

    def test_upload_item_user_does_not_exist(self):
        """测试上传物品时用户不存在的情况"""
        data = {
            "title": "Test Item",
            "username": "nonexistent@example.com",
            "price_lower_bound": "10.00",
            "price_upper_bound": "20.00",
            "meta_info": {"author": "Author Name", "description": "Test description"},
            "picture": None,
        }
        response = self.client.post(self.upload_url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is not logged in", response.data["non_field_errors"])

    def test_upload_item_user_not_logged_in(self):
        """测试上传物品时用户未登录的情况"""
        # 确保用户未登录
        self.client.logout()
        data = {
            "title": "Test Item",
            "username": self.test_user_email,
            "price_lower_bound": "10.00",
            "price_upper_bound": "20.00",
            "meta_info": {"author": "Author Name", "description": "Test description"},
            "picture": None,
        }
        response = self.client.post(self.upload_url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is not logged in", response.data["non_field_errors"])

    def test_upload_item_meta_info_uncomplete(self):
        """测试上传物品时meta_info不全的情况"""
        # 模拟用户登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "title": "Test Item",
            "username": self.test_user_email,
            "price_lower_bound": "10.00",
            "price_upper_bound": "20.00",
            "meta_info": {"author": "Author Name", "description": "Test description"},
            "picture": None,
        }
        response = self.client.post(self.upload_url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("meta_info", response.data)

    def test_upload_item_price_format_invalid(self):
        """测试上传物品时价格格式无效的情况"""
        # 模拟用户登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "title": "Test Item",
            "username": self.test_user_email,
            "price_lower_bound": "invalid_price",
            "price_upper_bound": "20.00",
            "meta_info": {"author": "Author Name", "description": "Test description", "course": "Course Name", "new": 1, "teacher": "Teacher Name"},
            "picture": None,
        }
        response = self.client.post(self.upload_url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price_lower_bound", response.data)

    def test_upload_item_meta_info_format_mismatch(self):
        """测试上传物品时meta_info格式不匹配的情况"""
        # 模拟用户登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "title": "Test Item",
            "username": self.test_user_email,
            "price_lower_bound": "10.00",
            "price_upper_bound": "20.00",
            "meta_info": {"author": "Author Name", "description": 123},  # 错误的格式
            "picture": None,
        }
        response = self.client.post(self.upload_url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("meta_info", response.data)

    def test_upload_item_success(self):
        """测试上传物品成功的情况"""
        # 模拟用户登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "title": "Test Item",
            "username": self.test_user_email,
            "price_lower_bound": "10.00",
            "price_upper_bound": "20.00",
            "meta_info": {"author": "Author Name", "description": "Test description", "course": "Course Name", "new": 1, "teacher": "Teacher Name"},
            "picture": None,
        }
        response = self.client.post(self.upload_url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Item uploaded successfully", response.data["message"])

    def test_search_items_title(self):
        """测试根据标题搜索物品"""
        data = {
            "content_type": "title",
            "search_keyword": "微积分教程",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_title:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查分页信息是否存在
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        # 检查搜索结果内容
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))

    def test_search_items_incomplete_title(self):
        """测试根据不完整标题搜索物品"""
        data = {
            "content_type": "title",
            "search_keyword": "微积分",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_incomplete_title:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))

    def test_search_items_course(self):
        """测试根据课程搜索物品"""
        data = {
            "content_type": "course",
            "search_keyword": "线性代数",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_course:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("线性代数" in str(item) for item in results))

    def test_search_items_teacher(self):
        """测试根据老师搜索物品"""
        data = {
            "content_type": "teacher",
            "search_keyword": "魏洋",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_teacher:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("魏洋" in str(item) for item in results))

    def test_search_items_username(self):
        """测试根据用户名搜索物品"""
        data = {
            "content_type": "username",
            "search_keyword": self.test_user_email,
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_username:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any(self.test_user_email in str(item) for item in results))
        self.assertTrue(any("微积分教程" in str(item) for item in results))
        self.assertTrue(any("线性代数入门" in str(item) for item in results))
        self.assertTrue(any("大学物理学" in str(item) for item in results))

    def test_search_items_author(self):
        """测试根据作者搜索物品"""
        data = {
            "content_type": "author",
            "search_keyword": "崔建莲",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_author:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("崔建莲" in str(item) for item in results))
        
    def test_search_items_description(self):
        """测试根据描述搜索物品"""
        data = {
            "content_type": "description",
            "search_keyword": "破损",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_description:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))

    def test_search_items_no_results(self):
        """测试搜索没有结果的情况"""
        data = {
            "content_type": "title",
            "search_keyword": "不存在的书籍",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_no_results:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回的 results 列表为空
        self.assertEqual(len(response.data["results"]), 0)
        
    def test_search_items_invalid_content_type(self):
        """测试搜索时提供无效的content_type"""
        data = {
            "content_type": "invalid_content_type",
            "search_keyword": "微积分教程",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_invalid_content_type:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid content_type", response.data["content_type"][0])

    def test_search_items_no_content_type(self):
        """测试搜索时提供空的content_type"""
        data = {
            "search_keyword": "微积分教程",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_no_content_type:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required.", response.data["content_type"][0])

    def test_search_items_no_search_keyword(self):
        """测试搜索时不提供search_keyword"""
        data = {
            "content_type": "title",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_no_search_keyword:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required.", response.data["search_keyword"][0])

    def test_search_items_empty_search_keyword(self):
        """测试搜索时提供空的search_keyword"""
        data = {
            "content_type": "title",
            "search_keyword": "",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_empty_search_keyword:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))
        self.assertTrue(any("线性代数入门" in str(item) for item in results))
        self.assertTrue(any("大学物理学" in str(item) for item in results))
        self.assertTrue(any("王振波" in str(item) for item in results))
    
    def test_search_items_homepage_user_logged(self):
        """测试搜索时加载homepage且传入user"""
        data = {
            "content_type": "homepage",
            "search_keyword": self.test_user_email,
            "search_all": True
        }
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_homepage_user_logged:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("线性代数入门" in str(item) for item in results))
        self.assertTrue(any("数字逻辑电路" in str(item) for item in results))
        self.assertTrue(any("tt" in str(item) for item in results))

    def test_search_items_homepage_user_logged_upload_curriculum(self):
        # login
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        # upload curriculum
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        schedule_data = {
            "username": self.test_user_email,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            schedule_data,
            format='multipart' 
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # search
        search_data = {
            "content_type": "homepage",
            "search_keyword": self.test_user_email,
            "search_all": True
        }
        response = self.client.get(self.search_url, search_data, format='json')
        print("test_search_items_homepage_user_logged_upload_curriculum:", response.data)
        # item0中meta_info里的teacher是赵有键，和课表中的老师匹配
        self.assertIn("数字逻辑与数字集成电路", str(response.data["results"]))

    def test_search_items_homepage_user_logged_raise_need(self):
        # login
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        # raise need
        need_data = {
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "线性代数", "teacher": "tt", "new": 7},
        }
        response = self.client.post(self.raise_need_url, need_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # search
        search_data = {
            "content_type": "homepage",
            "search_keyword": self.test_user_email,
            "search_all": True
        }
        response = self.client.get(self.search_url, search_data, format='json')
        print("test_search_items_homepage_user_logged_raise_need:", response.data)
        self.assertIn("线性代数", str(response.data["results"]))
    
    def test_search_items_homepage_user_logged_upload_schedule_raise_need(self):
        # login
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        # raise need
        need_data = {
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "线性代数", "teacher": "tt", "new": 8},
        }
        response = self.client.post(self.raise_need_url, need_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) 
        # upload curriculum
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        schedule_data = {
            "username": self.test_user_email,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            schedule_data,
            format='multipart' 
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)    

        # search
        search_data = {
            "content_type": "homepage",
            "search_keyword": self.test_user_email,
            "search_all": True
        }
        response = self.client.get(self.search_url, search_data, format='json')
        print("test_search_items_homepage_user_logged_raise_need:", response.data)   
        # 根据推荐算法，数字逻辑与数字集成电路推荐度最高
        self.assertIn("数字逻辑与数字集成电路", str(response.data["results"][0]['title']))

    def test_search_items_homepage_user_unlogged(self):
        """测试搜索时加载homepage且传入空的user"""
        data = {
            "content_type": "homepage",
            "search_keyword": "",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_homepage_user_unlogged:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))
        self.assertTrue(any("线性代数入门" in str(item) for item in results))
        self.assertTrue(any("大学物理学" in str(item) for item in results))
        self.assertTrue(any("王振波" in str(item) for item in results))

    def test_search_items_homepage_user_unlogged_but_deliver_email(self):
        """测试搜索时加载homepage且传入空的user"""
        data = {
            "content_type": "homepage",
            "search_keyword": self.test_user_email,
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_homepage_user_unlogged_but_deliver_email:", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is not logged in", response.data["non_field_errors"])
    
    def test_search_items_stop_words(self):
        """测试搜索时提供包含停用词的search_keyword"""
        data = {
            "content_type": "title",
            "search_keyword": "微积分教程",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_stop_words:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))
        self.assertTrue(any("微积分" in str(item) for item in results))
        self.assertFalse(any("线性代数入门" in str(item) for item in results))
        self.assertFalse(any("大学物理学" in str(item) for item in results))

    def test_search_items_picture(self):
        """测试搜索时返回图片URL"""
        data = {
            "content_type": "title",
            "search_keyword": "微积分教程",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_picture:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue("picture" in str(results[0]))
        self.assertTrue("微积分教程" in str(results[0]))

    def test_search_items_by_id(self):
        """测试根据ID搜索物品"""
        data = {
            "content_type": "id",
            "search_keyword": str(self.item1.id),
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_by_id:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))

    def test_search_items_by_user_items(self):
        """测试根据email精确搜索物品"""
        ## 登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "content_type": "user_items",
            "search_keyword": self.test_user_email,
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_by_user_items:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(any("微积分教程" in str(item) for item in results))
        self.assertTrue(any("大学物理学" in str(item) for item in results))
        self.assertTrue(any("王振波" in str(item) for item in results))
        self.assertFalse(any(self.test_user2_email in item['username'] for item in results))

    def test_search_items_by_id_not_found(self):
        """测试根据不存在的ID搜索物品"""
        data = {
            "content_type": "id",
            "search_keyword": "11",  # 假设不存在
        }
        response = self.client.get(self.search_url, data, format='json')
        print("test_search_items_by_id_not_found:", response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Item not found", response.data["message"])

    def test_search_items_pagination(self):
        """
        测试 search-items 接口分页功能：
        - 创建额外物品使总数超过默认 page_size（12）
        - 检查第一页返回的 count、next、previous 和 results
        - 根据 next URL 请求第二页，并验证返回数据的正确性
        """
        # 在原有物品基础上，额外创建 15 个物品，确保总数 > 12
        for i in range(15):
            Item.objects.create(
                title=f"Bulk Item {i}",
                username=self.test_user_email,
                price_lower_bound=10.0,
                price_upper_bound=20.0,
                user=self.test_user,
                meta_info={"description": "Bulk Item"},
                picture=None,
            )
        data = {
            "content_type": "title",
            "search_keyword": "",
        }
        response = self.client.get(self.search_url, data, format='json')
        print("第一页分页结果:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        # 检查总数是否正确（原有 6 个 + 15 个新增 = 20）
        self.assertEqual(response.data["count"], 21)
        # 默认页大小为 12，所以第一页的 results 长度应为 12
        self.assertEqual(len(response.data["results"]), 12)
        # 第一页的 previous 应为 None，next 不为空
        self.assertIsNone(response.data["previous"])
        self.assertIsNotNone(response.data["next"])
        
        # 使用 next URL 继续请求第二页
        next_url = response.data["next"]
        # 通过客户端直接请求 next_url（注意：next_url 是完整的 URL）
        response_next = self.client.get(next_url, format='json')
        print("第二页分页结果:", response_next.data)
        self.assertEqual(response_next.status_code, status.HTTP_200_OK)
        # 第二页返回的结果数量应为剩余 (21 - 12 = 9)
        self.assertEqual(len(response_next.data["results"]), 9)
        # 第二页的 previous 不为空，next 应为 None（如果数据刚好结束）
        self.assertIsNotNone(response_next.data["previous"])
        self.assertIsNone(response_next.data["next"])

        # 构造原始URL + ?page=2 或 &page=2
        page_url = f"{self.search_url}?content_type=title&search_keyword=&page=2"
        response_direct_page = self.client.get(page_url)
        print("直接请求第二页:", response_direct_page.data)
        self.assertEqual(response_direct_page.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_direct_page.data["results"]), 9)
        
        # 比较两种方式获取的第二页数据是否一致
        self.assertEqual(
            [item['id'] for item in response_next.data["results"]],
            [item['id'] for item in response_direct_page.data["results"]]
        )

        # 测试page=3
        page_url = f"{self.search_url}?content_type=title&search_keyword=&page=3"
        response_page_3 = self.client.get(page_url)
        print("直接请求第三页:", response_page_3.data)
        self.assertEqual(response_page_3.status_code, status.HTTP_404_NOT_FOUND)
        ## 判断{'detail': ErrorDetail(string='Invalid page.', code='not_found')}
        self.assertIn("Invalid page", response_page_3.data["detail"])

    def test_modify_items(self):
        """测试修改物品"""
        # 模拟用户登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "id": self.item1.id,
            "title": "Updated Item",
            "username": self.test_user_email,
            "price_lower_bound": "15.00",
            "price_upper_bound": "25.00",
            "meta_info": {"author": "Updated Author", "description": "Updated description", "course": "Updated Course", "new": 3, "teacher": "Updated Teacher"},
            "picture": None,
            "remove": False,
        }
        response = self.client.post(reverse('modify-items'), data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Item modified successfully", response.data["message"])
        # 验证物品是否被修改
        item = Item.objects.get(id=self.item1.id)
        self.assertEqual(item.title, "Updated Item")
        self.assertEqual(item.price_lower_bound, 15.00)
        self.assertEqual(item.price_upper_bound, 25.00)
        self.assertEqual(item.meta_info["author"], "Updated Author")
        self.assertEqual(item.meta_info["description"], "Updated description")
        self.assertEqual(item.meta_info["course"], "Updated Course")
        self.assertEqual(item.meta_info["new"], 3)
        self.assertEqual(item.meta_info["teacher"], "Updated Teacher")
        self.assertTrue(bool(item.picture))  # 检查 picture 是否为空
        self.assertEqual(item.username, self.test_user_email)

    def test_modify_items_not_found(self):
        """测试修改物品时物品不存在的情况"""
        # 模拟用户登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "id": 9999,  # 假设这个ID不存在
            "title": "Updated Item",
            "username": self.test_user_email,
            "price_lower_bound": "15.00",
            "price_upper_bound": "25.00",
            "meta_info": {"author": "Updated Author", "description": "Updated description", "course": "Updated Course", "new": 5, "teacher": "Updated Teacher"},
            "picture": None,
            "remove": False,
        }
        response = self.client.post(reverse('modify-items'), data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Item not found", response.data["message"])

    def test_delete_items_success(self):
        """测试删除物品"""
        # 模拟用户登录
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "id": self.item1.id,
            "username": self.test_user_email,
        }
        response = self.client.post(reverse('delete-items'), data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Item deleted successfully", response.data["message"])
        # 验证物品是否被删除
        with self.assertRaises(Item.DoesNotExist):
            Item.objects.get(id=self.item1.id)

    def test_delete_items_user_not_match(self):
        self.client.login(
            email=self.test_user2_email,
            password=self.test_user2_password,
        )
        data = {
            "id": self.item1.id,
            "username": self.test_user2_email,
        }
        response = self.client.post(reverse('delete-items'), data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You do not have permission to delete this item.", response.data["non_field_errors"])
        # 验证物品仍然存在
        item = Item.objects.get(id=self.item1.id)
        self.assertEqual(item.title, "微积分教程")

class SoldItemsTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.test_user_email = "testuser_sold@example.com"
        self.test_user_password = "testpassword123"
        self.test_user = User.objects.create_user(
            email=self.test_user_email,
            username="testsold",
            password=self.test_user_password,
        )
        self.test_user2_email = "testuser2_sold@example.com"
        self.test_user2_password = "testpassword2222"
        self.test_user2 = User.objects.create_user(
            email=self.test_user2_email,
            username="testsold2",
            password=self.test_user2_password,
        )
        
        # 创建未售出测试物品
        self.unsold_item = Item.objects.create(
            title="未售出的物品",
            username=self.test_user_email,
            price_lower_bound=20,
            price_upper_bound=25.00,
            user=self.test_user,
            meta_info={"author": "测试作者", "course": "测试课程", "teacher": "测试教师", "description": "这是一个未售出的测试物品", "new": 9},
            picture=None,
            sold=False
        )
        
        # 创建已售出测试物品
        self.sold_item = Item.objects.create(
            title="已售出的物品",
            username=self.test_user_email,
            price_lower_bound=15.00,
            price_upper_bound=20.00,
            user=self.test_user,
            meta_info={"author": "测试作者", "course": "测试课程", "teacher": "测试教师", "description": "这是一个已售出的测试物品", "new": 8},
            picture=None,
            sold=True
        )
        
        # 设置测试URLs
        self.search_url = reverse('search-items')
        self.modify_url = reverse('modify-items')
        self.delete_url = reverse('delete-items')
        
    def tearDown(self):
        # 确保每次测试后用户登出
        self.client.logout()
        
    def test_search_items_exclude_sold(self):
        """测试搜索物品时默认排除已售出物品"""
        data = {
            "content_type": "title",
            "search_keyword": "测试物品",
        }
        response = self.client.get(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        
        # 验证只返回未售出物品
        self.assertEqual(len(results), 1)
        self.assertIn("未售出的物品", str(results))
        self.assertNotIn("已售出的物品", str(results))
    
    def test_search_by_id_include_sold(self):
        """测试通过ID搜索时应返回已售出物品"""
        data = {
            "content_type": "id",
            "search_keyword": str(self.sold_item.id),
        }
        response = self.client.get(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        
        # 验证可以通过ID找到已售出物品
        self.assertEqual(len(results), 1)
        self.assertIn("已售出的物品", str(results))
    
    def test_search_user_items_include_sold(self):
        """测试查看用户物品时应包含已售出物品"""
        # 登录用户
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        data = {
            "content_type": "user_items",
            "search_keyword": self.test_user_email,
        }
        response = self.client.get(self.search_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        
        # 验证用户物品包含已售出物品
        self.assertEqual(len(results), 1)
        self.assertTrue(any("未售出的物品" in str(item) for item in results))
        self.assertFalse(any("已售出的物品" in str(item) for item in results))
    
    def test_modify_sold_item(self):
        """测试不允许修改已售出物品"""
        # 登录用户
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        
        # 尝试修改已售出物品
        data = {
            "id": self.sold_item.id,
            "title": "尝试修改已售出物品",
            "username": self.test_user_email,
            "price_lower_bound": "15.00",
            "price_upper_bound": "20.00",
            "meta_info": {"author": "更新作者", "description": "更新描述", "course": "更新课程", "new": 6, "teacher": "更新教师"},
            "picture": None,
            "remove": False,
        }
        response = self.client.post(self.modify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot modify a sold item", response.data["message"])
        
        # 验证物品未被修改
        item = Item.objects.get(id=self.sold_item.id)
        self.assertEqual(item.title, "已售出的物品")
    
    def test_delete_sold_item(self):
        """测试允许删除已售出物品"""
        # 登录用户
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        
        # 尝试删除已售出物品
        data = {
            "id": self.sold_item.id,
            "username": self.test_user_email,
        }
        response = self.client.post(self.delete_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Item deleted successfully", response.data["message"])
        
        # 验证物品已被删除
        with self.assertRaises(Item.DoesNotExist):
            Item.objects.get(id=self.sold_item.id)
    
    def test_find_matching_needs_exclude_sold(self):
        """测试find_matching_needs方法排除已售出物品"""
        # 创建一个测试需求
        need = Need.objects.create(
            title="未售出的物品",
            username=self.test_user2_email,
            price_lower_bound=10.00,
            price_upper_bound=30.00,
            user=self.test_user2,
            meta_info={"author": "测试作者", "course": "测试课程", "teacher": "测试教师"},
            is_fulfilled=False
        )
        
        # 使用模型的方法找匹配的物品
        matching_items = Item.objects.find_matching_items(need)
        
        # 验证只包含未售出物品
        self.assertEqual(len(matching_items), 1)
        self.assertEqual(matching_items[0].title, "未售出的物品")
    
    def test_get_need_matching_items_exclude_sold(self):
        """测试获取需求匹配物品时排除已售出物品"""
        # 创建一个测试需求
        need = Need.objects.create(
            title="未售出的物品",
            username=self.test_user2_email,
            price_lower_bound=10.00,
            price_upper_bound=30.00,
            user=self.test_user2,
            meta_info={"author": "测试作者", "course": "测试课程", "teacher": "测试教师"},
            is_fulfilled=False
        )
        
        # 登录用户
        self.client.login(
            email=self.test_user2_email,
            password=self.test_user2_password,
        )
        
        # 获取需求详情
        data = {
            "id": need.id
        }
        response = self.client.get(reverse('get-need'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查匹配的物品是否排除已售出物品
        if 'matching_items' in response.data:
            matching_items = response.data['matching_items']
            item_ids = [item['id'] for item in matching_items]
            self.assertIn(self.unsold_item.id, item_ids)
            self.assertNotIn(self.sold_item.id, item_ids)
    
    def test_update_purchase_with_sold_item(self):
        """测试不能用已售出物品创建购买请求"""
        # 登录用户
        self.client.login(
            email=self.test_user2_email,
            password=self.test_user2_password,
        )
        
        # 尝试使用已售出物品创建购买请求
        data = {
            "item_id": self.sold_item.id,
            "seller_id": self.test_user.id,
            "buyer_id": self.test_user2.id,
            "raiser_id": self.test_user2.id,
            "price": "17.50",
            "place": "测试地点",
            "time": "2025-05-20 14:00"
        }
        response = self.client.post(reverse('update-purchase'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This item has already been sold", response.data["message"])