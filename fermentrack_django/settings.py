"""
Django settings for fermentrack_django project.

Generated by 'django-admin startproject' using Django 1.10.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
from django.contrib.messages import constants as message_constants  # For the messages override
import datetime, pytz

from secretsettings import *  # See fermentrack_django/secretsettings.py.example, or run utils/make_secretsettings.sh

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']  # This is bad practice, but is the best that we're going to get given our deployment strategy


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app.apps.AppConfig',
    'constance',
    'constance.backends.database',
    'django_celery_beat',
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

ROOT_URLCONF = 'fermentrack_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'constance.context_processors.config'
            ],
        },
    },
]

WSGI_APPLICATION = 'fermentrack_django.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'collected_static'

MEDIA_URL = '/media/'
MEDIA_ROOT = 'media'

DATA_URL = '/data/'
DATA_ROOT = 'data'


# Constance configuration
# https://github.com/jazzband/django-constance

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_ADDITIONAL_FIELDS = {
    'date_time_display_select': ['django.forms.fields.ChoiceField', {  # Used in device_dashboard.html
        'widget': 'django.forms.Select',
        'choices': ((None, "-----"), ("mm/dd/yy", "mm/dd/yy"), ("dd/mm/yy", "dd/mm/yy"), ("yy-mm-dd", "yy-mm-dd"))
    }],
    'temperature_format_select': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((None, "-----"), ("F", "Fahrenheit"), ("C", "Celsius"))
    }],
    'git_update_type_select': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((None, "-----"),
                    ("any", "Prompt to upgrade on all commits/updates"),
                    ("tagged", "Prompt to upgrade on tagged (official, numbered) releases"),
                    ("none", "Do not automatically check/prompt for updates"))
    }],
}

# CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_CONFIG = {
    'BREWERY_NAME': ('Fermentrack', 'Name to be displayed in the upper left of each page', str),
    'DATE_TIME_FORMAT_DISPLAY': ('mm/dd/yy', 'How dates will be displayed in the dashboard',
                                 'date_time_display_select'),
    'REQUIRE_LOGIN_FOR_DASHBOARD': (False, 'Should a logged-out user be able to see device status?', bool),
    'TEMPERATURE_FORMAT': ('F', 'Preferred temperature format (can be overridden per device)',
                           'temperature_format_select'),
    'USER_HAS_COMPLETED_CONFIGURATION': (False, 'Has the user completed the configuration workflow?', bool),
    'LAST_GIT_CHECK': (pytz.timezone(TIME_ZONE).localize(datetime.datetime.now()),
                       'When was the last time we checked GitHub for upgrades?', datetime.datetime),
    'GIT_UPDATE_TYPE': ('any', 'What Fermentrack upgrades would you like to download?', 'git_update_type_select'),
    'ALLOW_GIT_BRANCH_SWITCHING': (False, 'Should the user be allowed to switch Git branches from within the app?',
                                   bool),
}



# Messages Configuration

# Overriding messages.ERROR due to it being named something different in Bootstrap 3
MESSAGE_TAGS = {
    message_constants.ERROR: 'danger'
}


# Decorator Configuration
LOGIN_URL = 'login'              # Used in @login_required decorator
CONSTANCE_SETUP_URL = 'setup_config'    # Used in @site_is_configured decorator

