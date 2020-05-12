import os, sys
from django.contrib.messages import constants as message_constants  # For the messages override
import datetime, pytz, configparser
#from git import Repo
import git

from .secretsettings import *  # See fermentrack_django/secretsettings.py.example, or run utils/make_secretsettings.sh

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

ALLOWED_HOSTS = ['*']  # This is bad practice, but is the best that we're going to get given our deployment strategy


# Check if Sentry is enabled (read in the config filepath)
CONFIG_INI_FILEPATH = os.path.join(BASE_DIR, 'fermentrack_django', 'config.ini')
config = configparser.ConfigParser()
config.read(CONFIG_INI_FILEPATH)
ENABLE_SENTRY = config.getboolean("sentry", "enable_sentry", fallback=True)

try:
    local_repo = git.Repo(path=BASE_DIR)
    GIT_BRANCH = local_repo.active_branch.name
except git.exc.InvalidGitRepositoryError:
    ENABLE_SENTRY = False
    GIT_BRANCH = 'dev'




# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app.apps.AppConfig',
    'firmware_flash.apps.AppConfig',
    'gravity.apps.GravityAppConfig',
    'external_push.apps.AppConfig',
    'constance',
    'constance.backends.database',
    'huey.contrib.djhuey',
]

if sys.platform == "darwin":
    # For the MacOS standalone support, we need mod_wsgi for Apache. Since I do most of my development/testing on
    # a Mac but don't use the standalone support, I don't want the app to get added if we don't have the packages
    # installed.
    import subprocess

    reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
    installed_packages = [r.decode().split('==')[0] for r in reqs.split()]
    if 'mod_wsgi' in installed_packages:
        INSTALLED_APPS += 'mod_wsgi.server', # Used for the macOS setup


# if ENABLE_SENTRY:
#     import raven
#     INSTALLED_APPS += 'raven.contrib.django.raven_compat',

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
                'constance.context_processors.config',
                'app.context_processors.preferred_tz',
                'app.context_processors.devices',
                # 'app.context_processors.devices',
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
                    ("dev", "Upgrade whenever possible, including 'beta' code"),
                    ("master", "Only upgrade when updates are officially released"),
                    ("none", "Do not automatically check/prompt for updates"))
    }],
    'timezone_select': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': [(x,x) for x in pytz.common_timezones]
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
    'TEMP_CONTROL_SUPPORT_ENABLED': (True, 'Has the user enabled support for temp tracking/control (eg BrewPi)?', bool),
    'GRAVITY_SUPPORT_ENABLED': (True, 'Has the user enabled support for specific gravity sensors?', bool),
    'LAST_GIT_CHECK': (pytz.timezone(TIME_ZONE).localize(datetime.datetime.now()),
                       'When was the last time we checked GitHub for upgrades?', datetime.datetime),
    'GIT_UPDATE_TYPE': ('dev', 'What Fermentrack upgrades would you like to download?', 'git_update_type_select'),
    'ALLOW_GIT_BRANCH_SWITCHING': (False, 'Should the user be allowed to switch Git branches from within the app?',
                                   bool),
    'FIRMWARE_LIST_LAST_REFRESHED': (pytz.timezone(TIME_ZONE).localize(datetime.datetime.now())+datetime.timedelta(hours=-25), 'When was the firmware list last refreshed from fermentrack.com?',
                                     datetime.datetime),
    'PREFERRED_TIMEZONE': ("UTC", 'What timezone would you prefer to use in Fermentrack?', 'timezone_select'),

    'GRAPH_BEER_TEMP_COLOR': ("#E3B505", 'What color do you want the beer temperature line on the graph?', str),
    'GRAPH_BEER_SET_COLOR': ("#203340", 'What color do you want the beer setting line on the graph?', str),
    'GRAPH_FRIDGE_TEMP_COLOR': ("#044B7F", 'What color do you want the fridge temperature line on the graph?', str),
    'GRAPH_FRIDGE_SET_COLOR': ("#107E7D", 'What color do you want the fridge setting line on the graph?', str),
    'GRAPH_ROOM_TEMP_COLOR': ("#610345", 'What color do you want the room temperature line on the graph?', str),
    'GRAPH_GRAVITY_COLOR': ("#95190C", 'What color do you want the specific gravity line on the graph?', str),
    'GRAPH_GRAVITY_TEMP_COLOR': ("#280003", 'What color do you want the gravity sensor temperature line on the graph?', str),
    'SQLITE_OK_DJANGO_2': (False, 'Has the Django 2.0+ SQLite migration been run?',
                                   bool),

}

CONSTANCE_CONFIG_FIELDSETS = {
    'General Options': ('BREWERY_NAME', 'DATE_TIME_FORMAT_DISPLAY', 'REQUIRE_LOGIN_FOR_DASHBOARD', 'TEMPERATURE_FORMAT',
                        'TEMP_CONTROL_SUPPORT_ENABLED', 'GRAVITY_SUPPORT_ENABLED', 'PREFERRED_TIMEZONE'),

    'Graph Colors': ('GRAPH_BEER_TEMP_COLOR', 'GRAPH_BEER_SET_COLOR', 'GRAPH_FRIDGE_TEMP_COLOR',
                     'GRAPH_FRIDGE_SET_COLOR', 'GRAPH_ROOM_TEMP_COLOR', 'GRAPH_GRAVITY_COLOR',
                     'GRAPH_GRAVITY_TEMP_COLOR'),

    'Internal Items': ('FIRMWARE_LIST_LAST_REFRESHED', 'LAST_GIT_CHECK', 'USER_HAS_COMPLETED_CONFIGURATION',
                       'SQLITE_OK_DJANGO_2'),

    'Advanced Options': ('ALLOW_GIT_BRANCH_SWITCHING','GIT_UPDATE_TYPE')
}



# Messages Configuration

# Overriding messages.ERROR due to it being named something different in Bootstrap 3
MESSAGE_TAGS = {
    message_constants.ERROR: 'danger'
}


# Decorator Configuration
LOGIN_URL = 'login'              # Used in @login_required decorator
CONSTANCE_SETUP_URL = 'setup_config'    # Used in @site_is_configured decorator


# Redis Configuration (primarily for gravity sensor support)
REDIS_HOSTNAME = "127.0.0.1"
REDIS_PORT = 6379
REDIS_PASSWORD = ""  # Not used for most installations. If you need this, yell in a thread & we'll add to Constance



# Huey Configuration
HUEY = {
    'name': 'fermentrack_huey',
    'store_none': False,
    'immediate': False,

    'connection': {
        'host': REDIS_HOSTNAME,
        'port': REDIS_PORT,
        'password': REDIS_PASSWORD,  # TODO - Check if this actually works
        'read_timeout': 1,
    }
}


if ENABLE_SENTRY:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn="http://3a1cc1f229ae4b0f88a4c6f7b5d8f394:c10eae5fd67a43a58957887a6b2484b1@sentry.optictheory.com:9000/2",
        integrations=[DjangoIntegration()],
        send_default_pii=True,
    )

    # RAVEN_CONFIG = {
    #     'dsn': 'http://3a1cc1f229ae4b0f88a4c6f7b5d8f394:c10eae5fd67a43a58957887a6b2484b1@sentry.optictheory.com:9000/2',
    #     # If you are using git, you can also automatically configure the
    #     # release based on the git info.
    #     'release': raven.fetch_git_sha(os.path.abspath(BASE_DIR)),
    #     'tags': {
    #         'branch': GIT_BRANCH
    #     },
    # }
