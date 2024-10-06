"""
Django settings for myproject project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-!08qm@gmvvk8=yqb6*5fo+jvca4(a@*ml3=wld^l8f3_pbwb$7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'myapp'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

X_FRAME_OPTIONS = 'ALLOW-FROM https://192.168.0.22'

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'myapp', 'templates')],
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

WSGI_APPLICATION = 'myproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'monitoring_db',          # 데이터베이스 이름
        'USER': 'postgres',          # PostgreSQL 사용자 이름
        'PASSWORD': 'coremax1@#',  # PostgreSQL 사용자 비밀번호
        'HOST': '192.168.0.42',             # 데이터베이스 서버 주소 (로컬호스트인 경우 'localhost')
        'PORT': '5432',                  # PostgreSQL 기본 포트
    },
    'mariadb_nova': {  # MySQL 또는 MariaDB 데이터베이스 설정
        'ENGINE': 'django.db.backends.mysql',  # MySQL/MariaDB 엔진
        'NAME': 'nova',  # MariaDB 데이터베이스 이름
        'USER': 'root',  # MariaDB 사용자 이름
        'PASSWORD': 'byN0BEXCoEKKrjkukW6YsUYto9OyZPF3KgYJTDVF',  # MariaDB 사용자 비밀번호
        'HOST': '10.0.0.10',  # MariaDB 서버 주소
        'PORT': '3306',  # MariaDB 기본 포트
    },
    'mariadb_glance': {  # MySQL 또는 MariaDB 데이터베이스 설정
        'ENGINE': 'django.db.backends.mysql',  # MySQL/MariaDB 엔진
        'NAME': 'glance',  # MariaDB 데이터베이스 이름
        'USER': 'root',  # MariaDB 사용자 이름
        'PASSWORD': 'byN0BEXCoEKKrjkukW6YsUYto9OyZPF3KgYJTDVF',  # MariaDB 사용자 비밀번호
        'HOST': '10.0.0.10',  # MariaDB 서버 주소
        'PORT': '3306',  # MariaDB 기본 포트
    },
    'mariadb_neutron': {  # MySQL 또는 MariaDB 데이터베이스 설정
        'ENGINE': 'django.db.backends.mysql',  # MySQL/MariaDB 엔진
        'NAME': 'neutron',  # MariaDB 데이터베이스 이름
        'USER': 'root',  # MariaDB 사용자 이름
        'PASSWORD': 'byN0BEXCoEKKrjkukW6YsUYto9OyZPF3KgYJTDVF',  # MariaDB 사용자 비밀번호
        'HOST': '10.0.0.10',  # MariaDB 서버 주소
        'PORT': '3306',  # MariaDB 기본 포트
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

# settings.py
SECURE_SSL_REDIRECT = True  # 모든 HTTP 요청을 HTTPS로 리다이렉트
SECURE_HSTS_SECONDS = 3600  # HSTS 설정 (HTTPS 전용)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # 하위 도메인에 HSTS 적용
SECURE_HSTS_PRELOAD = True  # HSTS Preload 리스트에 추가