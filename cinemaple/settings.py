"""
Django settings for cinemaple project.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import os
import warnings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY_DJANGO', '')
if not SECRET_KEY:
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()
    warnings.warn("SECRET_KEY_DJANGO not set – using a random key (sessions will reset on restart)")

# Mailchimp keys (optional – if unset, mailing list features are disabled)
MAILCHIMP_API_KEY = os.environ.get('MAILCHIMP_API_KEY', '')
MAILCHIMP_DATA_CENTER = os.environ.get('MAILCHIMP_DATA_CENTER', '')
MAILCHIMP_EMAIL_LIST_ID = os.environ.get('MAILCHIMP_EMAIL_LIST_ID', '')
MAILCHIMP_EMAIL_LIST_ID_TEST = os.environ.get('MAILCHIMP_EMAIL_LIST_ID_TEST', '')

# Mailgun keys (optional – if unset, email is sent via console backend / not sent)
MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN_NAME = os.environ.get('MAILGUN_DOMAIN_NAME', '')

# Recaptcha keys (required for registration forms; leave empty to skip captcha in dev)
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')

# Secret salts for email verification and password reset
EMAIL_VERIFICATION_SECRET_SALT = os.environ.get('EMAIL_VERIFICATION_SECRET_SALT', 'change-me')
PW_RESET_SECRET_SALT = os.environ.get('PW_RESET_SECRET_SALT', 'change-me')

REV_USER_ACCESS_SECRET_SALT = os.environ.get('REV_USER_ACCESS_SECRET_SALT', 'change-me')

# TMDb
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')

# Email: use Mailgun if configured and package installed, otherwise console (emails printed to logs)
if MAILGUN_API_KEY and MAILGUN_DOMAIN_NAME:
    try:
        import django_mailgun  # noqa: F401
        EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
        MAILGUN_ACCESS_KEY = MAILGUN_API_KEY
        MAILGUN_SERVER_NAME = MAILGUN_DOMAIN_NAME
    except ImportError:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = 'admin@cinemaple.com'

# automatically run in debug mode if in production
ENVIRONEMENT = os.environ.get('DJANGO_ENV', 'DEBUG')


if ENVIRONEMENT == "DEBUG":
    DEBUG = True
    CORS_ORIGIN_ALLOW_ALL = True
elif ENVIRONEMENT == "PRODUCTION":
    DEBUG = False

ALLOWED_HOSTS = [
    'www.cinemaple.com',
    'cinemaple.com',
    '.onrender.com',
    'localhost',
    '127.0.0.1',
]
# Allow extra hosts from env (comma-separated) for other platforms
if os.environ.get('ALLOWED_HOSTS_EXTRA'):
    ALLOWED_HOSTS.extend(h.strip() for h in os.environ['ALLOWED_HOSTS_EXTRA'].split(','))

# Application definition

INSTALLED_APPS = [
    'userhandling.apps.UserhandlingConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'django_recaptcha',
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
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
import dj_database_url

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True,
    )


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'cinemaple/staticfiles')
STATIC_URL = '/static/'


# Simplified static file serving via whitenoise.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}


# Define my home IP in order to use UserBasedExceptionMiddleware
INTERNAL_IPS = ["84.254.94.123"]

LOGIN_REDIRECT_URL = '/curr_mov_nights'
LOGIN_URL = '/login/'


LOGOUT_REDIRECT_URL = '/'

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

# Django 3.2+: set default auto field to avoid warnings
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Prefixes for Mailchimp Tags
MC_PREFIX_LOCPERMID = "locpermid_"
MC_PREFIX_HASACCESSID = "hasaccessid_"
