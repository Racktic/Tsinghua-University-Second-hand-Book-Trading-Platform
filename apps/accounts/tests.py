from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User, EmailVerification

class AccountsTests(APITestCase):
      def setUp(self):
            # 创建测试用户
            self.test_user_email = "testuser@mails.tsinghua.edu.cn"
            self.test_user_password = "testpassword123"
            self.test_user = User.objects.create_user(
                  email=self.test_user_email,
                  username=self.test_user_email,
                  password=self.test_user_password,
            )
            self.check_activate_url = reverse('check-active')
      def tearDown(self):
            # 用户登出
            self.client.logout()

      def test_register_success(self):
            """测试成功注册"""
            url = reverse('register')
            # 确保 email 和 code 匹配
            EmailVerification.objects.create(email='newuser@mails.tsinghua.edu.cn', code='123456')
            data = {'email': 'newuser@mails.tsinghua.edu.cn', 'password': 'newpassword123', 'code': '123456'}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(User.objects.filter(email='newuser@mails.tsinghua.edu.cn').count(), 1)

      def test_register_user_already_exists(self):
            """测试注册已存在用户"""
            EmailVerification.objects.create(email=self.test_user_email, code='123456')
            url = reverse('register')
            data = {'email': self.test_user_email, 'password': 'newpassword123','code':'123456'}
            response = self.client.post(url, data, format='json')
            print("response.data:", response.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

      def test_register_invalid_data(self):
            """测试注册无效数据"""
            url = reverse('register')
            data = {'email': '', 'password': '', 'code': ''}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

      def test_register_invalid_email(self):
            """测试注册无效邮箱"""
            url = reverse('register')
            data = {'email': 'invalidemail', 'password': 'newpassword123', 'code': '123456'}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

      def test_register_verification_code_not_match(self):
            """测试注册错误验证码"""
            url = reverse('register')
            EmailVerification.objects.create(email='newuser@example.com', code='123456')
            data = {'email': 'newuser@example.com', 'password': 'newpassword123', 'code': '123111'}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(User.objects.filter(email='newuser@example.com').count(), 0)

      def test_register_invalid_verification_code(self):
            """测试注册无效验证码"""
            url = reverse('register')
            EmailVerification.objects.create(email='newuser123@example.com', code='123456')
            data = {'email': 'newuser123@example.com', 'password': 'newpassword123', 'code': '6543210dfdsf'}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(User.objects.filter(email='newuser@example.com').count(), 0)

      def test_login_success(self):
            """测试登录成功"""
            url = reverse('login')
            data = {'email': self.test_user_email, 'password': self.test_user_password}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('user', response.data)

      def test_login_user_already_logged_in(self):
            """测试用户已登录"""
            url = reverse('login')
            data = {'email': self.test_user_email, 'password': self.test_user_password}
            response = self.client.post(url, data, format='json')
            
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
 
      def test_login_invalid_credentials(self):
            """测试登录无效凭据"""
            url = reverse('login')
            data = {'email': self.test_user_email, 'password': 'wrongpassword'}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

      def test_login_invalid_data(self):
            """测试登录无效数据"""
            url = reverse('login')
            data = {'email': '', 'password': ''}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

      def test_login_user_not_found(self):
            """测试登录用户不存在"""
            url = reverse('login')
            data = {'email': 'nonexistent@example.com', 'password': 'password123'}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

      def test_logout_success(self):
            """测试登出成功"""
            url = reverse('logout')
            self.client.force_login(self.test_user)
            response = self.client.post(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            ## 检查用户是否已登出

      def test_logout_without_login(self):
            """测试未登录时登出"""
            url = reverse('logout')
            response = self.client.post(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

      def test_user_logged_in(self):
            """测试用户已登录"""
            logged_in= self.client.login(email=self.test_user_email, password=self.test_user_password)
            self.assertTrue(logged_in, "User should be logged in")
            response = self.client.get(self.check_activate_url, {'username': self.test_user_email})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

      def test_user_not_logged_in(self):
            """测试用户未登录"""
            response = self.client.get(self.check_activate_url, {'username': self.test_user_email})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


      def test_user_does_not_exist(self):
            """测试用户不存在"""
            response = self.client.get(self.check_activate_url, {'username': 'nonexistent@example.com'})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

      def test_email_not_provided(self):
            """测试未提供 email 参数"""
            response = self.client.get(self.check_activate_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


