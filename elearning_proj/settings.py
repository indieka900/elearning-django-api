from datetime import timedelta
from pathlib import Path
from tzlocal import get_localzone
from dotenv import load_dotenv
import os
import logging
# Build paths inside the project like this: BASE_DIR / 'subdir'.

# Load .env file
load_dotenv()

def str_to_bool(value):
    return value.lower() in ['true', '1', 't', 'y', 'yes']
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DEFAULT_HOST = 'www'

ALLOWED_HOSTS = []

ROOT_HOSTCONF = "elearning_proj.hosts"

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    "corsheaders",
    'drf_yasg',
    "django_hosts",
    "rest_framework",
    "rest_framework_simplejwt",
    'django_rest_passwordreset',
    'easyaudit',
    'elearning',
    'notifications',
    'payments',
    'user_auth'
]

AUTH_USER_MODEL = 'user_auth.CustomUser'

MIDDLEWARE = [
    # Default Django middleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Django Hosts middleware
    "django_hosts.middleware.HostsRequestMiddleware",
    "django_hosts.middleware.HostsResponseMiddleware",
    # Whitenoise middleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # CORS middleware
    "corsheaders.middleware.CorsMiddleware",
    # Easy Audit middleware
    'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
    # Two Factor middleware
    'django_otp.middleware.OTPMiddleware',
    #'axes.middleware.AxesMiddleware',
     'user_auth.middleware.DeviceMiddleware',
     #'django_user_agents.middleware.UserAgentMiddleware',

]


ROOT_URLCONF = 'elearning_proj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'elearning_proj.wsgi.application'

WSGI_APPLICATION = "elearning_proj.wsgi.application"
ASGI_APPLICATION = "elearning_proj.asgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_DATABASE'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '3306'),  # default MySQL port if not set
    }
}

# Rest Framework settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.IsAdminUser",
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),     
    
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=100),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

#Verifying Password Hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "static"

STATIC_FILES_DIRS = [STATIC_ROOT]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CAMPUS_EMAIL = os.environ.get('CAMPUS_EMAIL')
# ACADEMY_EMAIL = os.environ.get('ACADEMY_EMAIL')
# BOOKINGS_EMAIL = os.environ.get('BOOKINGS_EMAIL')
# INTERN_EMAIL = os.environ.get('INTERN_EMAIL')
# SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_USE_TLS = str_to_bool(os.environ.get('EMAIL_USE_TLS', 'False'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

#payments update
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE')

# M-pesa
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
MPESA_EXPRESS_SHORTCODE = os.environ.get('MPESA_SHORTCODE')
MPESA_SHORTCODE= os.environ.get('MPESA_SHORTCODE')
MPESA_SHORTCODE_TYPE = 'paybill'
MPESA_INITIATOR_USERNAME = 'testapi'
MPESA_INITIATOR_SECURITY_CREDENTIAL = 'Safaricom999!*!'
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL')
MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT')
MPESA_PARTYB = os.environ.get('MPESA_PARTYB')