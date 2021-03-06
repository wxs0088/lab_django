"""
Django settings for lab_django project.

Generated by 'django-admin startproject' using Django 2.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '18-xdffk=jn^n4iegl49ws@lxp@m99%-i$@0i1$#%7tn*a%z@w'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
APPEND_SLASH=False
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # haystack要放在应用的上面
    'haystack',
    'labapp.apps.LabappConfig',
    # 跨域
    'corsheaders',
    'rest_framework',
    'channels',
]
CHANNEL_LAYERS = {
  'default': {
    'BACKEND': 'channels_redis.core.RedisChannelLayer',
    'CONFIG': {
      "hosts": [('120.26.175.79', 6379)],
    },
  },
}
# 设置跨域
CORS_ALLOW_CREDENTIALS = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 跨域
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lab_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')]
        ,
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

WSGI_APPLICATION = 'lab_django.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lab',
        'USER': 'root',  # 用户名
        'PASSWORD': '000000',  # 密码
        'HOST': '120.26.175.79',  # 数据库主机，默认为localhost
        'PORT': '3306',  # 数据库端口，MySQL默认为3306
        'OPTIONS': {
            'autocommit': True,
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/



STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# 定义上传文件夹的路径
UPLOAD_ROOT = os.path.join(BASE_DIR, 'static/upload')


import datetime
JWT_AUTH = {
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),
    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'labapp.user.jwt_response_payload_handler',  # 重新login登录返回函数
}

REST_FRAMEWORK = {
    # 身份认证
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),

#全局配置JWT验证设置
# 'DEFAULT_PERMISSION_CLASSES': (
#             'rest_framework.permissions.IsAuthenticated',
#         ),
}

AUTHENTICATION_BACKENDS = [
    'labapp.user.UsernameMobileAuthBackend',
]


AUTH_USER_MODEL = 'labapp.User'


EMAIL_USE_SSL = True  # Secure Sockets Layer 安全套接层, 取决于邮件服务器是否开启加密协议
EMAIL_HOST = 'smtp.qq.com'  # 邮件服务器地址 ， 如果是163改成smtp.163.com
EMAIL_PORT = 465  # 邮件服务器端口
EMAIL_HOST_USER = '1349157185@qq.com'  # 登陆邮件服务器的账号
EMAIL_HOST_PASSWORD = 'zdcyocfdngqfhcde'  # 登陆邮件服务器的授权密码
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER  # 邮件的发送者
#
# # 允许哪些人可以请求你和请求方式
CORS_ORIGIN_ALLOW_ALL = True  # 改为true是所有人都可以访问我


# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  #email后端
# EMAIL_USE_TLS = False   #是否使用TLS安全传输协议
# EMAIL_USE_SSL = True    #是否使用SSL加密，qq企业邮箱要求使用
# EMAIL_HOST = 'smtp.exmail.qq.com'   #发送邮件的邮箱 的 SMTP服务器，这里用了qq企业邮箱
# EMAIL_PORT = 465     #发件箱的SMTP服务器端口
# EMAIL_HOST_USER = 'h4055874@163.com'    #发送邮件的邮箱地址
# EMAIL_HOST_PASSWORD = 'yt1230.+'         #发送邮件的邮箱密码
import lab_django
ASGI_APPLICATION = 'lab_django.routing.application'


'''配置haystack '''
# 全文检索框架配置
HAYSTACK_CONNECTIONS = {
    'default': {
        # 指定whoosh引擎
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        # 'ENGINE': 'jsapp.whoosh_cn_backend.WhooshEngine',      # whoosh_cn_backend是haystack的whoosh_backend.py改名的文件为了使用jieba分词
        # 索引文件路径
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    }
}
# 添加此项，当数据库改变时，会自动更新索引，非常方便
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
