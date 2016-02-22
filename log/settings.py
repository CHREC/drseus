from os.path import abspath, dirname

BASE_DIR = dirname(dirname(abspath(__file__)))
SECRET_KEY = 'y8o)jsiw&89zg5jqg1h9$iweu9$(mf78)l*=vsmfkqc-4hab1#'
DEBUG = True
ROOT_URLCONF = 'log.urls'
STATIC_URL = '/static/'

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'django_tables2',
    'django_filters',
    'log',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates/'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'drseus',
        'USER': 'drseus',
        'PASSWORD': 'drseus',
        'HOST': 'localhost',
        'PORT': '',
    }
}
