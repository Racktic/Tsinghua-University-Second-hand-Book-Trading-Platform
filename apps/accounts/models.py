from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from apps.chat.models import ChatRoom
from django.core.validators import RegexValidator
# Create your models here.

class User(AbstractUser):
      # You can add custom fields here, such as phone number or address
      class Meta:
            app_label = 'accounts'
      email_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9._%+-]+@mails\.tsinghua\.edu\.cn$',
            message='邮箱必须是清华大学邮箱(@mails.tsinghua.edu.cn)'
      )
      email = models.EmailField(
            max_length=100, 
            unique=True,
            validators=[email_validator]
      )
      password = models.CharField(max_length=100)
      created_at = models.DateTimeField(auto_now_add=True)    
      updated_at = models.DateTimeField(auto_now=True)
      class_schedule = models.JSONField(default=list, blank=True)

      USERNAME_FIELD = 'email'
      REQUIRED_FIELDS = []

      def __str__(self):
            return self.username                                             
class EmailVerification(models.Model):
      email_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9._%+-]+@mails\.tsinghua\.edu\.cn$',
            message='邮箱必须是清华大学邮箱(@mails.tsinghua.edu.cn)'
      )
      
      email = models.EmailField(
            unique=True,
            validators=[email_validator]
      )
      code = models.CharField(max_length=6)  # 验证码
      created_at = models.DateTimeField(default=now)  # 验证码创建时间

      def __str__(self):
            return f"{self.email} - {self.code}"