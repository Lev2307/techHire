from pathlib import Path
import os

from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get('DEBUG'))

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',

    'apps.accounts',
    'apps.vacancies',
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

CSRF_TRUSTED_ORIGINS = [os.environ.get('TUNNEL_DOMAIN')]

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('POSTGRES_ENGINE'),
        'NAME': os.environ.get('POSTGRES_NAME'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
        'CONN_MAX_AGE': int(os.environ.get('POSTGRES_CONN_MAX_AGE'))
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'accounts.Applicant'

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TELEGRAM_BOT_ID = os.environ.get('TELEGRAM_BOT_ID')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

CELERY_BROKER_URL = os.environ.get('REDIS_URL')
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")
CELERY_TIMEZONE = os.environ.get('TZ')

RECOMMENDED_VACANCIES_LIFETIME_IN_HOURS = 12

CELERY_BEAT_SCHEDULE = {
    "auto_updating_vacancies": {
        "task": "apps.vacancies.tasks.auto_updating_vacancies",
        "schedule": crontab(minute='0', hour=f'*/{RECOMMENDED_VACANCIES_LIFETIME_IN_HOURS}')
    }
}

SPECIALIZATIONS_LIST = [
    'Backend-разработка',
    'Frontend-разработка',
    'Fullstack-разработка',
    'Мобильная разработка', 
    'Машинное обучение/Нейросети',
    'ML-инженер',
    'Data-инженер',
    'Data Science',
    'Big Data',
    'DevOps', 
    'Системный аналитик',
    'QA/Тестирование',
    'Кибербезопасность',
    'Системное администрирование',
    'UI/UX',
    'Разработчик игр',
]

TECHNOLOGIES_LIST = [
    'Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C++', 'Go', 'Rust', 'PHP', 'Swift', 'Kotlin', # ЯП
    'React', 'Vue', 'Angular', 'Next.js', 'HTML/CSS', 'Tailwind/SASS', # front
    'Node.js', 'Django/FastAPI', 'Spring Boot', 'Laravel', 'GraphQL', 'REST', # back
    'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', # db
    'Docker', 'Kubernetes', 'Git', 'Linux', 'CI/CD', # инфраструктуры
    'PyTorch/TensorFlow', 'Pandas/NumPy', 'Spark', 'Airflow', # ml
    'Kafka', 'RabbitMQ', # брокеры сообщений
]

SUPERJOB_API_KEY = os.environ.get('SUPERJOB_API_SECRET_KEY')

HH_API_CLIENT_ID = os.environ.get('HH_API_CLIENT_ID')
HH_API_CLIENT_SECRET = os.environ.get('HH_API_CLIENT_SECRET')
HH_API_ACCESS_TOKEN = os.environ.get("HH_API_ACCESS_TOKEN")

PROXY_URL = os.environ.get("PROXY_URL")
TELEGRAM_ID_FOR_TESTS = os.environ.get("TELEGRAM_ID_FOR_TESTS")

# 1. пофиксить или же выяснить работу celery_beat_schedule после обновления кода ✅
# 2. если всё устроит в рекомендациях (подчернуто) ✅
# 2.1 тесты к рекомендациям (helpers -> taska -> recommendations) (практически готово) ✅
# 3. Делаю логин через тг (all-auth) + после логина добавляю привязку специальностей и инструментов с почтой. ✅
# 4. Добавление собственных инструментов к себе на аккаунт + /accounts/profile (страница настроек пользователя + изменение их) ✅
# 5. 3+4 в тесты ✅
# 6. Создание api ✅
# 7. Тесты api ✅
# 8. Уведы в тг при появлении новой вакансии в рекомендациях ✅
# 9. Создание укороченного функционала в тг (профиль, избранные вакансии)
# 10. Конец бэкэнда!!!!!