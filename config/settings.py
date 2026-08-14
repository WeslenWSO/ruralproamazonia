from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# No Render, variáveis do painel devem prevalecer sobre .env local.
load_dotenv(BASE_DIR / ".env", encoding="utf-8", override=False)

from clientes.social_auth import montar_socialaccount_providers

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-gtq5y6)#ctb76hel%*d9+k@!0#8&q_0(r1-ycio4*g$e(1el@j',
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

ON_RENDER = bool(
    os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    or os.environ.get('RENDER', '').lower() in ('true', '1', 'yes')
)
if not DEBUG and ON_RENDER:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.apple',
    'allauth.socialaccount.providers.facebook',
    'ckeditor',
    'core',
    'servicos',
    'blog',
    'contato',
    'clientes.apps.ClientesConfig',
    'buscarrural',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_config',
                'contato.context_processors.whatsapp_inscricao_form',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


def _obter_database_url():
    for key in (
        'DATABASE_URL',
        'POSTGRES_URL',
        'INTERNAL_DATABASE_URL',
        'RENDER_DATABASE_URL',
    ):
        valor = os.environ.get(key, '').strip()
        if valor:
            return valor

    usuario = (
        os.environ.get('POSTGRES_USER', '').strip()
        or os.environ.get('PGUSER', '').strip()
    )
    senha = (
        os.environ.get('POSTGRES_PASSWORD', '').strip()
        or os.environ.get('PGPASSWORD', '').strip()
    )
    host = (
        os.environ.get('POSTGRES_HOST', '').strip()
        or os.environ.get('PGHOST', '').strip()
    )
    porta = (
        os.environ.get('POSTGRES_PORT', '').strip()
        or os.environ.get('PGPORT', '').strip()
        or '5432'
    )
    banco = (
        os.environ.get('POSTGRES_DB', '').strip()
        or os.environ.get('PGDATABASE', '').strip()
    )
    if usuario and senha and host and banco:
        return f'postgresql://{usuario}:{senha}@{host}:{porta}/{banco}'
    return ''


def _postgres_ssl_require(url):
    if 'sslmode=disable' in url:
        return False
    if 'sslmode=require' in url:
        return True
    host = url.split('@')[-1] if '@' in url else url
    if host.startswith('dpg-') or '/dpg-' in url:
        if '.render.com' not in host and 'postgres.render.com' not in host:
            return False
    return url.startswith('postgres')


_sqlite_path = BASE_DIR / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _sqlite_path,
    }
}

database_url = _obter_database_url()
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

if database_url:
    DATABASES['default'] = dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        ssl_require=_postgres_ssl_require(database_url),
    )
    if _sqlite_path.exists():
        DATABASES['legacy'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': _sqlite_path,
        }
elif ON_RENDER:
    DATABASES['default']['NAME'] = _sqlite_path

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Manaus'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SITE_BASE_URL = os.environ.get('SITE_BASE_URL', 'http://127.0.0.1:8000').strip().rstrip('/')
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', '').strip()

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'clientes:login'
LOGIN_REDIRECT_URL = 'clientes:painel'
LOGOUT_REDIRECT_URL = 'core:home'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_ADAPTER = 'clientes.adapters.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'clientes.adapters.SocialAccountAdapter'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_PROVIDERS = montar_socialaccount_providers()

SELENIUM_HEADLESS = os.environ.get("SELENIUM_HEADLESS", "False") == "True"
SELENIUM_CAPTCHA_TIMEOUT = int(os.environ.get("SELENIUM_CAPTCHA_TIMEOUT", "300"))

# Google Gemini — parecer BuscarRural (chave só no .env, nunca no Git)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash").strip()

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source'],
        ],
        'height': 300,
        'width': '100%',
    },
}
