import os
import pymysql
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'
ALLOWED_HOSTS = ['*']

# =================================================================
# APPS
# =================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'BACKEND',
    'FRONTEND',
    'django_recaptcha',
    'django.contrib.humanize'
]

# =================================================================
# MIDDLEWARE
# =================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# =================================================================
# TEMPLATES
# =================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
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

WSGI_APPLICATION = 'config.wsgi.application'

# =================================================================
# DATABASE (PROTEGIDA)
# =================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', character_set_connection=utf8mb4",
            'charset': 'utf8mb4',
        }
    }
}

# =================================================================
# AUTHENTICATION CONFIG
# =================================================================
AUTH_USER_MODEL = 'FRONTEND.Usuarios'
LOGIN_URL = '/mi-cuenta/'
LOGIN_REDIRECT_URL = '/dashboard/' 
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = [
    'BACKEND.backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# =================================================================
# CONFIGURACIÓN DE CORREO (PROTEGIDA)
# =================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_UTF8 = True

EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASS')
DEFAULT_FROM_EMAIL = f'BOGOCARGO <{os.getenv("EMAIL_USER")}>'

# =================================================================
# RECAPTCHA (PROTEGIDA)
# =================================================================
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE')

# =================================================================
# INTERNACIONALIZACIÓN Y OTROS
# =================================================================
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SEGURIDAD HTTPS (SOLO SI DEBUG=FALSE)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG

