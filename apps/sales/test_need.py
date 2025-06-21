from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import User
from apps.sales.models import Need


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
        self.need1 = Need.objects.create(
            title="微积分教程",
            username=self.test_user_email,
            price_lower_bound=20,
            price_upper_bound=25.00,
            user=self.test_user,
            meta_info={"author": "崔建莲", "course": "微积分A", "teacher": "崔建莲", "new": 9},
        )

        self.need2 = Need.objects.create(
            title="线性代数入门",
            username=self.test_user_email,
            price_lower_bound=15.00,
            price_upper_bound=23.45,
            user=self.test_user,
            meta_info={"author": "梁鑫", "course": "线性代数", "teacher": "史灵生", "new": 6},
        )

        self.need3 = Need.objects.create(
            title="大学物理学",
            username=self.test_user_email,
            price_lower_bound=20.01,
            price_upper_bound=27.54,
            user=self.test_user,
            meta_info={"author": "张三慧", "course": "大学物理B", "teacher": "魏洋", "new": 7},
        )

        self.need4 = Need.objects.create(
            title="微积分",
            username=self.test_user_email,
            price_lower_bound=15.00,
            price_upper_bound=23.45,
            user=self.test_user,
            meta_info={"author": "章纪民", "course": "微积分A", "teacher": "王振波", "new": 4},
        )
        self.need5 = Need.objects.create(
            title = "tt",
            username = self.test_user2_email,
            price_lower_bound = 20.01,
            price_upper_bound = 27.54,
            user = self.test_user2,
            meta_info = {"author": "tt", "course": "tt", "teacher": "tt", "new": 3},
        )

        self.raise_need_url = reverse("raise-need")
        self.modify_need_url = reverse("modify-need")
        self.delete_need_url = reverse("delete-need")
        self.check_need_url = reverse("user-needs")
        self.get_need_url = reverse("get-need")

    def tearDown(self):
        # 确保每次测试后用户登出
        self.client.logout()
        print("Tear down: User logged out.")

    def test_upload_need_success(self):
        # 测试上传需求成功
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt", "new": 2},
        }
        response = self.client.post(self.raise_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print("Upload need success test passed.")

    def test_upload_need_invalid_data_title_miss(self):
        # 测试上传需求失败（title缺失）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "title": "",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt", "new": 3},
        }
        response = self.client.post(self.raise_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_need_no_new(self):
        # 测试上传需求成功（meta_info缺失new字段）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "title": "数据库",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt"},
        }
        response = self.client.post(self.raise_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查数据库中是否成功创建了需求
        self.assertTrue(Need.objects.filter(title="数据库", username=self.test_user_email).exists())

    def test_upload_need_invalid_data_meta_info_empty(self):
        # 测试上传需求失败（meta_info为空）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {},
        }
        response = self.client.post(self.raise_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_need_invalid_data_meta_info_miss_field(self):
        # 测试上传需求失败（meta_info内部字段缺失）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "new": 5},
        }
        response = self.client.post(self.raise_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("teacher", response.data["meta_info"][0])

    def test_check_need_success(self):
        # 测试查看需求成功
        login_successful = self.client.login(email=self.test_user_email, password=self.test_user_password)
        self.assertTrue(login_successful, "Login failed. Check user credentials.")
        response = self.client.get(self.check_need_url, {'username': self.test_user_email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        self.assertEqual(response.data[0]['title'], "微积分教程")
        self.assertEqual(response.data[1]['title'], "线性代数入门")
        self.assertEqual(response.data[2]['title'], "大学物理学")
        self.assertEqual(response.data[3]['title'], "微积分")

    def test_check_need_invalid_data_username(self):
        # 测试查看需求失败（username缺失）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        response = self.client.get(self.check_need_url, {'username': "dfvdfgfd@example.com"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email mismatch with session user", response.data['non_field_errors'][0])

    def test_modify_need_success(self):
        # 测试修改需求成功
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "id": self.need1.id,
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt", "new": 8},
        }
        response = self.client.post(self.modify_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        modified_need = Need.objects.get(id=self.need1.id)
        self.assertEqual(modified_need.title, "线性代数")

    def test_modify_need_user_do_not_exist(self):
        # 测试修改需求失败（用户不存在）
        self.client.login(email="wawawa@example.com", password="sdfsfsdf")
        data = {
            "id": self.need1.id,
            "title": "线性代数",
            "username": "wawawa@example.com",
            "price_lower_bound": 15.00, 
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt", "new": 7},
        }
        response = self.client.post(self.modify_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is not logged in", response.data['non_field_errors'][0])
    
    def test_modify_need_user_do_not_login(self):
        # 测试修改需求失败（用户未登录）
        data = {
            "id": self.need1.id,
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt", "new": 4},
        }
        response = self.client.post(self.modify_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is not logged in", response.data['non_field_errors'][0])

    def test_modify_need_id_not_found(self):
        # 测试修改需求失败（需求ID未找到）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "id": 99999,  # 假设这个ID不存在
            "title": "线性代数",
            "username": self.test_user_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt", "new": 5},
        }
        response = self.client.post(self.modify_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Need not found", response.data['message'])
    def test_modify_need_id_user_not_match(self):
        # 测试修改需求失败（需求ID与用户不匹配）
        self.client.login(email=self.test_user2_email, password=self.test_user2_password)
        data = {
            "id": self.need1.id,
            "title": "线性代数",
            "username": self.test_user2_email,
            "price_lower_bound": 15.00,
            "price_upper_bound": 23.45,
            "meta_info": {"author": "tt", "course": "tt", "teacher": "tt", "new": 6},
        }
        response = self.client.post(self.modify_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You do not have permission to modify this need", response.data['message'])
    
    def test_get_need_success(self):
        # 测试获取需求成功
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "id": self.need1.id,
        }
        response = self.client.get(self.get_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "微积分教程")
        self.assertEqual(response.data['username'], self.test_user_email)

    def test_get_need_id_not_found(self):
        # 测试获取需求失败（需求ID未找到）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "id": 99999,  # 假设这个ID不存在
        }
        response = self.client.get(self.get_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Need not found", response.data['message'])

    def test_get_need_invalid_data_format(self):
        # 测试获取需求失败（请求格式错误）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "id": "invalid_id",  # 非法ID格式
        }
        response = self.client.get(self.get_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A valid integer is required.", response.data['id'][0])

    def test_delete_need_success(self):
        # 测试删除需求成功
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "username": self.test_user_email,
            "id": self.need1.id,
        }
        response = self.client.post(self.delete_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Need.objects.filter(id=self.need1.id).exists())

    def test_delete_need_user_not_match(self):
        # 测试删除需求失败（需求ID与用户不匹配）
        self.client.login(email=self.test_user2_email, password=self.test_user2_password)
        data = {
            "username": self.test_user2_email,
            "id": self.need1.id,
        }
        response = self.client.post(self.delete_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You do not have permission to delete this need", response.data['non_field_errors'][0])

    def test_delete_need_id_not_found(self):
        # 测试删除需求失败（需求ID未找到）
        self.client.login(email=self.test_user_email, password=self.test_user_password)
        data = {
            "username": self.test_user_email,
            "id": 99999,  # 假设这个ID不存在
        }
        response = self.client.post(self.delete_need_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Need does not exist", response.data['non_field_errors'][0])