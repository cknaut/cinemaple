"""
Django settings for cinemaple project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

import django_heroku

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY_DJANGO']

# Mailchimp keys

MAILCHIMP_API_KEY = os.environ['MAILCHIMP_API_KEY']
MAILCHIMP_DATA_CENTER = os.environ['MAILCHIMP_DATA_CENTER']
MAILCHIMP_EMAIL_LIST_ID = os.environ['MAILCHIMP_EMAIL_LIST_ID']
MAILCHIMP_EMAIL_LIST_ID_TEST = os.environ['MAILCHIMP_EMAIL_LIST_ID_TEST']

# Mailgun keys
MAILGUN_API_KEY = os.environ['MAILGUN_API_KEY']
MAILGUN_DOMAIN_NAME = os.environ['MAILGUN_DOMAIN_NAME']

# Recaptcha keys
RECAPTCHA_PRIVATE_KEY = os.environ['RECAPTCHA_SECRET_KEY']
RECAPTCHA_PUBLIC_KEY = os.environ['RECAPTCHA_SITE_KEY']

# Secret SAlt for email registration
EMAIL_VERIFICATION_SECRET_SALT = os.environ['EMAIL_VERIFICATION_SECRET_SALT']
PW_RESET_SECRET_SALT = os.environ['PW_RESET_SECRET_SALT']

REV_USER_ACCESS_SECRET_SALT = os.environ['REV_USER_ACCESS_SECRET_SALT']

# TMDb
TMDB_API_KEY = os.environ['TMDB_API_KEY']

EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
MAILGUN_ACCESS_KEY = MAILGUN_API_KEY
MAILGUN_SERVER_NAME = MAILGUN_DOMAIN_NAME

DEFAULT_FROM_EMAIL = 'admin@cinemaple.com'

# automatically run in debug mode if in production
ENVIRONEMENT = os.environ['DJANGO_ENV']


if ENVIRONEMENT == "DEBUG":
    DEBUG = True
    CORS_ORIGIN_ALLOW_ALL = True
elif ENVIRONEMENT == "PRODUCTION":
    DEBUG = False

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'userhandling.apps.UserhandlingConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_nose',
    'corsheaders',
    'captcha',
    'bootstrap_datepicker_plus',
    'bootstrap3',
    'tinymce',
    'rest_framework',
    'django_social_share',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'cinemaple.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [' ',
                 os.path.join(BASE_DIR, 'userhandling/templates'),
                 ],
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

WSGI_APPLICATION = 'cinemaple.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.' +
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.' +
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.' +
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.' +
                'NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

# https://devcenter.heroku.com/articles/django-assets
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'cinemaple/staticfiles')
STATIC_URL = '/static/'


# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Define my home IP in order to use UserBasedExceptionMiddleware
INTERNAL_IPS = ["84.254.94.123"]

django_heroku.settings(locals())


LOGIN_REDIRECT_URL = '/curr_mov_nights'
LOGIN_URL = '/login/'


LOGOUT_REDIRECT_URL = '/'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

CORS_ORIGIN_ALLOW_ALL = True


if ENVIRONEMENT == "DEBUG":
    SECURE_SSL_REDIRECT = False
elif ENVIRONEMENT == "PRODUCTION":
    SECURE_SSL_REDIRECT = True


REST_FRAMEWORK = {

    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

# Prefixes for Mailchimp Tags
MC_PREFIX_LOCPERMID = "locpermid_"
MC_PREFIX_HASACCESSID = "hasaccessid_"
