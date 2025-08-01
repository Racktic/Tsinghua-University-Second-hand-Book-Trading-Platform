"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import json
from pathlib import Path
import os
import sys
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)5_lrwwi5j&4j65b=jly^+24o&r)wsv$7k#p37rw3gpe@fh%al'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://BookGather-frontend-BookGather.app.spring25a.secoder.net",
    "https://BookGather-frontend-BookGather.app.spring25a.secoder.net",
    "http://bookgather-frontend-bookgather.app.spring25a.secoder.net",
    "https://bookgather-frontend-bookgather.app.spring25a.secoder.net",
    "http://frontend-dev-bookgather.app.spring25a.secoder.net",
    "https://frontend-dev-bookgather.app.spring25a.secoder.net",
]


# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'apps.accounts',
    'apps.sales',
    'apps.chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('Redis.BookGather.secoder.local', 6379)],  # Redis 地址和端口
        },
    },
}
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


if os.getenv('DEPLOY')!=None and os.path.isfile("config/config.json"):
    with open("config/config.json", "r") as file:
        env = json.load(file)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env['Database']['name'],
        'USER': env['Database']['user'],
        'PASSWORD': env['Database']['password'],
        'HOST': env['Database']['host'],
        'PORT': env['Database']['port'],
        'OPTIONS': {'charset': 'utf8mb4'},
    },
} if os.getenv('DEPLOY')!=None else {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default backend
]

AUTH_USER_MODEL = 'accounts.User'  # 指定自定义用户模型

# 邮件后端配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 使用 SMTP 后端

# SMTP 服务器配置
EMAIL_HOST = 'smtp.163.com'  # 替换为你的邮件服务提供商的 SMTP 服务器地址
EMAIL_PORT = 25  # SMTP 端口号（通常为 587 或 465）
EMAIL_USE_TLS = True  # 是否使用 TLS 加密
EMAIL_USE_SSL = False  # 如果使用 SSL，加密端口通常为 465


if os.getenv('DEPLOY')!=None and os.path.isfile('config/config.json'):
    with open('config/config.json', 'r') as f:
        env = json.load(f)
        EMAIL_HOST_USER = env['EMAIL_HOST_USER']
        EMAIL_HOST_PASSWORD = env['EMAIL_HOST_PASSWORD']
        DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

MEDIA_URL = '/media/'
MEDIA_ROOT = '/opt/tmp/media'  

# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication", 
    ],

}
