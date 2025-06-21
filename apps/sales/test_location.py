from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class LocationTestCase(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.test_user_email_1 = "testuser1_location@example.com"
        self.test_user_password_1 = "testpassword123"
        self.test_user_1 = User.objects.create_user(
            email=self.test_user_email_1,
            username="testuser1_location",
            password=self.test_user_password_1,
        )

        self.test_user_email_2 = "testuser2_location@example.com"
        self.test_user_password_2 = "testpassword1234"
        self.test_user_2 = User.objects.create_user(
            email=self.test_user_email_2,
            username="testuser2_location",
            password=self.test_user_password_2,
        )
        self.test_user_email_3 = "haha@example.com"
        self.recommend_location_url = reverse('recommend_location')

    def tearDown(self):
        # 确保每次测试后用户登出
        self.client.logout()
        print("Tear down: User logged out.")

    def test_find_location_success(self):
        # first upload user1's class schedule
        self.client.login(email=self.test_user_email_1, password=self.test_user_password_1)
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        data = {
            "username": self.test_user_email_1,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Class schedule uploaded successfully", response.data["message"])

        # then upload user2's class schedule
        self.client.login(email=self.test_user_email_2, password=self.test_user_password_2)
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule2.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule2.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )
        
        data = {
            "username": self.test_user_email_2,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Class schedule uploaded successfully", response.data["message"])
        # then test recommend location
        response = self.client.get(self.recommend_location_url, {'seller_email': self.test_user_email_1, 'buyer_email': self.test_user_email_2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)
        recommended_location_sample = {
            'location': '六教',
            'time': '星期一第2节'
        }
        self.assertIn(recommended_location_sample, response.data)

    def test_find_location_no_class_schedule(self):
        # first upload user1's class schedule
        self.client.login(email=self.test_user_email_1, password=self.test_user_password_1)
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        data = {
            "username": self.test_user_email_1,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Class schedule uploaded successfully", response.data["message"])

        # but user2 has no class schedule
        self.client.login(email=self.test_user_email_2, password=self.test_user_password_2)
        # then test recommend location
        response = self.client.get(self.recommend_location_url, {'seller_email': self.test_user_email_1, 'buyer_email': self.test_user_email_2})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)   

    def test_find_location_user_not_exist(self):
        # first upload user1's class schedule
        self.client.login(email=self.test_user_email_1, password=self.test_user_password_1)
        file_path = os.path.join(os.path.dirname(__file__), 'test_schedule.xls')
        with open(file_path, 'rb') as f:
            test_file = SimpleUploadedFile(
                name='test_schedule.xls',
                content=f.read(),
                content_type='application/vnd.ms-excel'
            )

        data = {
            "username": self.test_user_email_1,
            "class_schedule": test_file,  
        }
        response = self.client.post(
            reverse('upload_class_schedule'),
            data,
            format='multipart' 
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Class schedule uploaded successfully", response.data["message"])

        # test user2 not exist
        response = self.client.get(self.recommend_location_url, {'seller_email': self.test_user_email_1, 'buyer_email': self.test_user_email_3})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
