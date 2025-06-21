from django.shortcuts import render
from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import random
import string
import os
import json
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from .serializers import RegisterSerializer, LoginSerializer, VerifyEmailSerializer, CheckActivateSerializer
from apps.accounts.models import EmailVerification


class RegisterView(APIView):
      def post(self, request, *args, **kwargs):
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                  # email = serializer.validated_data['email']
                  # password = serializer.validated_data['password']
                  user = serializer.save()
                  return Response(
                        {"message": "User registered successfully"},
                        status=status.HTTP_201_CREATED
                  )
            errors = serializer.errors

            # RegisterView 中的错误处理逻辑
            if 'email' in errors:
                  if 'User already exists' in str(errors['email']):
                        return Response(
                              {"message": "user with this email already exists."},
                              status=status.HTTP_409_CONFLICT
                        )
                  if '邮箱必须是清华大学邮箱' in str(errors['email']):
                        return Response(
                              {"message": "邮箱必须是清华大学邮箱(@mails.tsinghua.edu.cn)"},
                              status=status.HTTP_400_BAD_REQUEST
                        )

            # 如果是验证码无效或不匹配，返回 400 状态码
            if 'code' in errors:
                  if 'Invalid verification code' in errors['code']:
                        return Response(
                              {"message": "Invalid verification code"},
                              status=status.HTTP_400_BAD_REQUEST
                        )
                  if 'Verification code does not match' in errors['code']:
                        return Response(
                              {"message": "Verification code does not match"},
                              status=status.HTTP_400_BAD_REQUEST
                        )
            # 其他验证错误，返回 400 状态码
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

import requests

class VerifyEmailView(APIView):
      def post(self, request, *args, **kwargs):
            serializer = VerifyEmailSerializer(data=request.data)
            if serializer.is_valid():
                  email = serializer.validated_data['email']
                  try:
                        api_key = None
                        # 检查是否在部署环境，并加载配置文件
                        if os.getenv('DEPLOY') is not None and os.path.isfile('config/config.json'):
                              with open('config/config.json', 'r') as f:
                                    env = json.load(f)
                                    api_key = env.get('API_KEY')  # 使用 get 方法避免 KeyError
                        
                        # 如果 api_key 未定义，抛出异常
                        if not api_key:
                              return Response(
                                    {"message": "API_KEY is not configured in config/config.json"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                              )
                        response = requests.get(f'https://api.hunter.io/v2/email-verifier', params={
                              'email': email,
                              'api_key': api_key
                        })
                        data = response.json()
                        if data['data']['status'] == 'valid':
                        # 如果邮箱有效，发送验证邮件
                              code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                              EmailVerification.objects.update_or_create(
                                    email=email,
                                    defaults={'code': code, 'created_at': now()}
                              )
                              try:
                                    sent_count = send_mail(
                                    'Email Verification Code',
                                    f'Your verification code is {code}',
                                    settings.EMAIL_HOST_USER,
                                    [email],
                                    fail_silently=False
                                    )
                                    if sent_count > 0:
                                          return Response(
                                                {"message": "Verification email sent successfully"},
                                                status=status.HTTP_200_OK
                                          )
                                    else:
                                          return Response(
                                                {"message": "Failed to send verification email"},
                                                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                                          )
                              except Exception as e:
                                    return Response(
                                    {"message": f"An error occurred while sending email: {str(e)}"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                                    )
                        else:
                              return Response(
                                    {"message": "Invalid email address, unable to send verification email"},
                                    status=status.HTTP_400_BAD_REQUEST
                              )
                  except Exception as e:
                        return Response(
                              {"message": f"Error verifying email: {str(e)}"},
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
            errors = serializer.errors
            # 处理邮箱格式错误
            if 'email' in errors and '邮箱必须是清华大学邮箱' in str(errors['email']):
                  return Response(
                        {"message": "邮箱必须是清华大学邮箱(@mails.tsinghua.edu.cn)"},
                        status=status.HTTP_400_BAD_REQUEST
                  )
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)



class LoginView(APIView):
      def post(self, request, *args, **kwargs):
                  # 检查用户是否已经登录
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                  user = serializer.validated_data['user']
                  login(request, user)
                  return Response({
                        "message": "Login successful",
                        "user": {
                              "email": user.email,
                              "username": user.username
                        }
                  }, status=status.HTTP_200_OK)
            return Response(
                  {"message": "Invalid credentials"},
                  status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(APIView):
      def post(self, request, *args, **kwargs):
            logout(request)
            # 检查用户是否已经登出
            if request.user.is_authenticated:
                  return Response(
                        {"message": "Logout failed, user is still logged in"},
                        status=status.HTTP_400_BAD_REQUEST  # 返回 400 状态码，表示登出失败
                  )
            return Response(
                  {"message": "Logout successful"},
                  status=status.HTTP_200_OK
            )

class CheckActivateView(APIView):
      def get(self, request, *args, **kwargs):
            serializer = CheckActivateSerializer(data=request.query_params, context= {'request': request})
            if serializer.is_valid():
                  return Response(
                        status=status.HTTP_200_OK # 用户已登录
                  )
            else: 
                  return Response(
                        status=status.HTTP_401_UNAUTHORIZED ## 用户未登录
                  )
            
