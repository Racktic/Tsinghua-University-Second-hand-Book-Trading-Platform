from rest_framework import serializers
from apps.accounts.models import User,EmailVerification
from django.contrib.auth import authenticate
from apps.sales.serializers import verify_user_is_online


class RegisterSerializer(serializers.ModelSerializer):
      code = serializers.CharField(write_only=True)
      class Meta:
            model = User
            fields = ('email','password','code')
            extra_kwargs = {'password': {'write_only': True}}
      def validate_email(self, value):
            if not value.endswith('@mails.tsinghua.edu.cn'):
                  raise serializers.ValidationError('邮箱必须是清华大学邮箱(@mails.tsinghua.edu.cn)')
            if User.objects.filter(email=value).exists():
                  raise serializers.ValidationError('User already exists')
            return value
      def validate_code(self, value):
            if len(value) != 6:
                  raise serializers.ValidationError('Invalid verification code')
            if EmailVerification.objects.filter(email=self.initial_data['email'], code=value).exists():
                  return value
            else:
                  raise serializers.ValidationError('Verification code does not match')

      def create(self, validated_data):
            validated_data.pop('code', None)  # Remove code from validated_data
            user = User.objects.create_user(
                  email=validated_data['email'],
                  username=validated_data['email'],
                  password=validated_data['password'],
                  # is_active=False  # 用户注册时默认不激活
            )
            return user

class LoginSerializer(serializers.Serializer):
      email = serializers.EmailField()
      password = serializers.CharField(write_only=True)

      def validate(self, data):
            email = data.get('email')
            password = data.get('password')
            if email and password:
                  user = authenticate(request=self.context.get('request'), username=email, password=password)
                  if not user:
                        raise serializers.ValidationError('Invalid email or password.')
            else:
                  raise serializers.ValidationError('Must include "email" and "password".')
            data['user'] = user
            return data

class VerifyEmailSerializer(serializers.Serializer):
      email = serializers.EmailField()

      def validate(self, data):
            email = data.get('email')
            if not email.endswith('@mails.tsinghua.edu.cn'):
                  raise serializers.ValidationError('邮箱必须是清华大学邮箱(@mails.tsinghua.edu.cn)')
            if User.objects.filter(email=email).exists():
                  raise serializers.ValidationError('User has already been verified')
            return data

class CheckActivateSerializer(serializers.Serializer):
      username = serializers.EmailField()

      def validate(self, data):
            request = self.context.get('request')
            email = data.get('username')
            data['user'] = verify_user_is_online(email, request)
            return data