from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import User
from apps.sales.models import Item
import os
from django.core.files.uploadedfile import SimpleUploadedFile


class UploadItemsTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.test_user_email = "testuser_upload@example.com"
        self.test_user_password = "testpassword123"
        self.test_user = User.objects.create_user(
            email=self.test_user_email,
            username="testuser",
            password=self.test_user_password,
        )
        self.test_user2_email = "testuser2_upload@example.com"
        self.test_user2_password = "testpassword2222"
        self.test_user2 = User.objects.create_user(
            email=self.test_user2_email,
            username="testuser2",
            password=self.test_user2_password,
        )
        # 创建测试物品
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
            username=self.test_user_email,
            price_lower_bound=15.00,
            price_upper_bound=23.45,
            user=self.test_user,
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
        self.courses = [
            {
                'course': '数据挖掘',
                'teacher': '李涓子',
                'location': '舜德/经管西楼102',
                'day': '星期四',
                'section': '第1节'
            },
            {
                'course': '微积分',
                'teacher': '张三',
                'location': '三教2302',
                'day': '星期二',
                'section': '第2节'
            }
        ]
        self.search_url = reverse('search-items')  
        self.upload_url = reverse('upload-items') 

    def tearDown(self):
        # 确保每次测试后用户登出
        self.client.logout()
        print("Tear down: User logged out.")

    def test_upload_class_schedule_success(self):
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        # data is an .xls file
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        data = {
            "username": self.test_user_email,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Class schedule uploaded successfully", response.data["message"])
        # 验证用户的课程表是否被正确保存
        user = User.objects.get(email=self.test_user_email)
        self.assertTrue(user.class_schedule)
        # 验证课程表的内容是否正确
        expected_course = {
            'course': '数据挖掘',
            'teacher': '李涓子',
            'location': '舜德/经管西楼',
            'day': '星期四',
            'section': '第1节'
        }

        # 你可以用assertIn检测预期课程是否在已保存的列表中
        self.assertIn(expected_course, user.class_schedule)
        

    def test_upload_class_schedule_invalid_file(self):
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        # data is a .txt file
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.txt')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.txt',
                content=f.read(),
                content_type='text/plain'
            )

        data = {
            "username": self.test_user_email,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_class_schedule_item_correct(self):
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        # data is an .xls file
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        data = {
            "username": self.test_user_email,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Class schedule uploaded successfully", response.data["message"])

        # get the class schedule
        response = self.client.get(reverse('upload_class_schedule'))
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        course_example = {'course': '数据挖掘', 'teacher': '李涓子', 'location': '舜德/经管西楼', 'day': '星期四', 'section': '第1节'}
        self.assertIn(course_example, response.data)

    def test_class_extraction_failed(self):
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        # data is an .xls file
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule_extraction_fail_sample.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule_extraction_fail_sample.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        data = {
            "username": self.test_user_email,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Class schedule extraction failed", response.data["message"])

class UploadClassScheduleDictTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.test_user_email = "testuser_dict@example.com"
        self.test_user_password = "testpassword123"
        self.test_user = User.objects.create_user(
            email=self.test_user_email,
            username="testuser_dict",
            password=self.test_user_password,
        )
    def tearDown(self):
        # 确保每次测试后用户登出
        self.client.logout()
        print("Tear down: User logged out.")
    
    def test_upload_schedule_dict_missing_email(self):
        # 没有传入 email 字段
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        payload = {
            "courses": [
                {"course": "数学", "teacher": "张老师", "location": "舜德/经管西楼102", "day": "星期四", "section": "第1节"}
            ]
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        # 序列化器验证失败时返回 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("email", str(response.data))
    
    def test_upload_schedule_dict_invalid_email(self):
        # 使用一个不存在的 email
        payload = {
            "email": "nonexistent@example.com",
            "courses": [
                {"course": "数学", "teacher": "张老师", "location": "舜德/经管西楼102", "day": "星期四", "section": "第1节"}
            ]
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("User", str(response.data))
    def test_upload_schedule_dict_user_not_login(self):
        # 用户未登录
        payload = {
            "email": self.test_user_email,
            "courses": [
                {"course": "数学", "teacher": "张老师", "location": "舜德/经管西楼102", "day": "星期四", "section": "第1节"}
            ]
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("User is not logged in", str(response.data))

    def test_upload_schedule_dict_missing_courses(self):
        # 缺少 courses 字段
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        payload = {
            "email": self.test_user_email,
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("courses", str(response.data))
    
    def test_upload_schedule_dict_courses_not_list(self):
        # courses 不是列表
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        payload = {
            "email": self.test_user_email,
            "courses": "this should be a list"
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("message"), "Courses must be a list.")
    
    def test_upload_schedule_dict_element_not_dict(self):
        # courses 列表中的元素不是 dict
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        payload = {
            "email": self.test_user_email,
            "courses": [
                "not a dict",
                {"course": "数学", "teacher": "张老师", "location": "舜德/经管西楼102", "day": "星期四", "section": "第1节"}
            ]
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Each course element must be a dict", response.data.get("message", ""))
    
    def test_upload_schedule_dict_missing_required_key(self):
        # courses 中的某个元素缺少必需的键，例如缺少 teacher
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        payload = {
            "email": self.test_user_email,
            "courses": [
                {
                    "course": "数学",
                    # "teacher" key missing
                    "location": "舜德/经管西楼102",
                    "day": "星期四",
                    "section": "第1节"
                }
            ]
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing keys in course at index", response.data.get("message", ""))
    
    def test_upload_schedule_dict_success(self):
        # 正确的 payload
        self.client.login(
            email=self.test_user_email,
            password=self.test_user_password,
        )
        payload = {
            "email": self.test_user_email,
            "courses": [
                {
                    "course": "数学",
                    "teacher": "张老师",
                    "location": "舜德/经管西楼102",
                    "day": "星期四",
                    "section": "第1节"
                },
                {
                    "course": "英语",
                    "teacher": "李老师",
                    "location": "三教2301",
                    "day": "星期二",
                    "section": "第3节"
                }
            ]
        }
        response = self.client.post(reverse('upload_class_schedule_dict'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Class schedule uploaded successfully", response.data.get("message", ""))
        
        # 验证数据库中该用户的 class_schedule 是否被更新
        user = User.objects.get(email=self.test_user_email)
        self.assertEqual(user.class_schedule, payload["courses"])

class CheckClassScheduleTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.test_user_email = "testuser_dict@example.com"
        self.test_user_password = "testpassword123"
        self.test_user = User.objects.create_user(
            email=self.test_user_email,
            username="testuser_dict",
            password=self.test_user_password,
        )
        self.check_schedule_url = reverse('check_class_schedule')  # 此处需确保urls.py中定义的路由名称为 check_class_schedule

    def tearDown(self):
        # 确保每次测试后用户登出
        self.client.logout()
        print("Tear down: User logged out.")

    def test_get_empty_schedule_with_login(self):
        """
        登录后，如果用户没有设置课表，则返回空列表
        """
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        response = self.client.get(self.check_schedule_url, {"email": self.test_user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])  # 没有设置时，返回 []

    def test_get_filled_schedule_with_login(self):
        """
        登录后，如果用户已经保存了课表，则返回课表数据
        """
        # 设置用户的 class_schedule 为包含一个课程的列表
        expected_course = {
            'course': '数据挖掘',
            'teacher': '李涓子',
            'location': '舜德/经管西楼102',
            'day': '星期四',
            'section': '第1节'
        }
        self.test_user.class_schedule = [expected_course]
        self.test_user.save()

        self.client.login(email=self.test_user_email, password=self.test_user_password)
        response = self.client.get(self.check_schedule_url, {"email": self.test_user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证返回数据包含预期课程
        self.assertIn(expected_course, response.data)

    def test_get_schedule_not_logged_in(self):
        """
        未登录时请求课表，应该返回认证失败错误
        """
        response = self.client.get(self.check_schedule_url, {"email": self.test_user_email})
        # 根据 CheckClassSchedule 视图及 verify_user_is_online 实现，返回错误码可能为 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 检查返回错误信息中包含提示“User is not logged in”或非字段错误标识
        self.assertIn("User is not logged in", str(response.data))

    