from pathlib import Path

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Sécurité
SECRET_KEY = 'django-insecure-b)e1g_9kl9ig@=(hs&xpq%y8==hl*)04vxptjg1e8ro(!8ohre'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authen',  # ton app
    'progression',

]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLs racine
ROOT_URLCONF = 'comautis.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR  / 'templates'],  # chemin vers templates
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

WSGI_APPLICATION = 'comautis.wsgi.application'

# Base de données (SQLite pour l’instant)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS/JS/Images)
STATIC_URL = '/static/'

# À AJOUTER À LA FIN DE settings.py

# Code secret pour l'inscription des éducateurs
# ⚠️ À CHANGER EN PRODUCTION !
EDUCATOR_SECRET_CODE = "COMAUTISTE2024"

# Configuration email (pour envoyer les notifications de validation)
# À configurer plus tard pour envoyer des vrais emails
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Pour tests

# Fichiers statiques (images, CSS, JS)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'authen' / 'static',
]
# *********
# URL de base pour accéder aux fichiers uploadés
MEDIA_URL = '/media/'

# Dossier physique où les fichiers seront stockés
MEDIA_ROOT = BASE_DIR / 'media'

# Taille maximale d'un fichier uploadé : 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB en bytes

# Taille maximale en mémoire pour les uploads : 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB en bytes

# Liste des extensions de fichiers autorisées pour l'upload
ALLOWED_UPLOAD_EXTENSIONS = [
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
    # Vidéos
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
    # Audio
    '.mp3', '.wav', '.ogg', '.m4a', '.aac',
    # Documents
    '.pdf', '.doc', '.docx', '.txt',
    # Autres
    '.zip', '.rar',
]

# Taille maximale pour chaque type de fichier (en MB)
MAX_UPLOAD_SIZE = {
    'image': 5,    # 5 MB pour les images
    'video': 50,   # 50 MB pour les vidéos
    'audio': 10,   # 10 MB pour les audios
    'document': 10,  # 10 MB pour les documents
}