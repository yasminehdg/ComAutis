import os
from pathlib import Path

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# ========================================
# 🔧 MODE DÉVELOPPEMENT LOCAL
# ========================================

# Sécurité
SECRET_KEY = 'django-insecure-b)e1g_9kl9ig@=(hs&xpq%y8==hl*)04vxptjg1e8ro(!8ohre'

# MODE DEBUG ACTIVÉ pour le développement
DEBUG = True

# ALLOWED_HOSTS pour le local UNIQUEMENT
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '::1']

# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authen',
    'forum',
    'paiement',
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
        'DIRS': [BASE_DIR / 'authen' / 'templates'],
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

# ========================================
# 💾 BASE DE DONNÉES LOCALE (SQLite)
# ========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validation des mots de passe (désactivée en local pour faciliter le dev)
AUTH_PASSWORD_VALIDATORS = []

# ========================================
# 🌍 INTERNATIONALISATION
# ========================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'  # Fuseau horaire français
USE_I18N = True
USE_TZ = True

# ========================================
# 📁 FICHIERS STATIQUES (CSS, JS, Images)
# ========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'forum' / 'static',
    BASE_DIR / 'authen' / 'static',  # Si tu as des fichiers statiques ici aussi
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ========================================
# 📤 FICHIERS MEDIA (uploads utilisateurs)
# ========================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========================================
# ⚙️ CONFIGURATION SPÉCIFIQUE
# ========================================

# Code secret pour l'inscription des éducateurs
EDUCATOR_SECRET_CODE = "COMAUTISTE2024"

# Configuration email (en console pour le développement)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Redirection après logout
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

# Clé par défaut pour les modèles
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========================================
# 🔒 SÉCURITÉ (Désactivée en local)
# ========================================
# Ces paramètres sont pour la production, on les désactive en local
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# ========================================
# 🐛 DEBUG TOOLBAR (optionnel mais utile)
# ========================================
# Décommenter si tu veux installer django-debug-toolbar
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

print("✅ Django en MODE LOCAL - DEBUG activé")
print(f"📁 Base de données: {DATABASES['default']['NAME']}")
print(f"🌐 Serveur: http://localhost:8000/")