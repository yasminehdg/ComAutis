#!/usr/bin/env python
"""
Script automatique pour configurer MEDIA dans Django
Usage: python configure_media.py
"""

import os
import sys
from pathlib import Path

def find_settings_file():
    """Trouve le fichier settings.py"""
    possible_paths = [
        'comautis/settings.py',
        'ComAutis/settings.py',
        'config/settings.py',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Chercher récursivement
    for root, dirs, files in os.walk('.'):
        if 'settings.py' in files and 'manage.py' in os.listdir('.'):
            return os.path.join(root, 'settings.py')
    
    return None

def find_urls_file():
    """Trouve le fichier urls.py principal"""
    settings_path = find_settings_file()
    if settings_path:
        urls_path = os.path.join(os.path.dirname(settings_path), 'urls.py')
        if os.path.exists(urls_path):
            return urls_path
    return None

def backup_file(filepath):
    """Crée une sauvegarde du fichier"""
    backup_path = filepath + '.backup'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Sauvegarde créée : {backup_path}")

def configure_settings():
    """Configure settings.py"""
    settings_path = find_settings_file()
    
    if not settings_path:
        print("❌ Fichier settings.py introuvable !")
        return False
    
    print(f"📄 Fichier trouvé : {settings_path}")
    
    # Lire le contenu
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si déjà configuré
    if 'MEDIA_URL' in content and 'MEDIA_ROOT' in content:
        print("ℹ️  MEDIA déjà configuré dans settings.py")
        return True
    
    # Créer une sauvegarde
    backup_file(settings_path)
    
    # Ajouter la configuration MEDIA
    media_config = """
# ============================================
# CONFIGURATION MEDIA (Fichiers uploadés)
# ============================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Limites de taille pour les uploads (10 MB max)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
"""
    
    # Ajouter après STATIC_URL
    if 'STATIC_URL' in content:
        # Trouver la position après STATIC_URL
        lines = content.split('\n')
        new_lines = []
        media_added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if "STATIC_URL = '/static/'" in line and not media_added:
                new_lines.append(media_config)
                media_added = True
        
        content = '\n'.join(new_lines)
    else:
        # Ajouter à la fin
        content += '\n' + media_config
    
    # Écrire le nouveau contenu
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Configuration MEDIA ajoutée à settings.py")
    return True

def configure_urls():
    """Configure urls.py"""
    urls_path = find_urls_file()
    
    if not urls_path:
        print("❌ Fichier urls.py principal introuvable !")
        return False
    
    print(f"📄 Fichier trouvé : {urls_path}")
    
    # Lire le contenu
    with open(urls_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si déjà configuré
    if 'settings.MEDIA_URL' in content or 'static(settings.MEDIA_URL' in content:
        print("ℹ️  MEDIA déjà configuré dans urls.py")
        return True
    
    # Créer une sauvegarde
    backup_file(urls_path)
    
    # Ajouter les imports si nécessaire
    imports_to_add = []
    
    if 'from django.conf import settings' not in content:
        imports_to_add.append('from django.conf import settings')
    
    if 'from django.conf.urls.static import static' not in content:
        imports_to_add.append('from django.conf.urls.static import static')
    
    if imports_to_add:
        # Trouver la dernière ligne d'import
        lines = content.split('\n')
        last_import_index = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                last_import_index = i
        
        # Insérer les nouveaux imports
        for imp in imports_to_add:
            lines.insert(last_import_index + 1, imp)
            last_import_index += 1
        
        content = '\n'.join(lines)
    
    # Ajouter le code de serving à la fin
    serving_code = """
# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
"""
    
    if not content.strip().endswith('\n'):
        content += '\n'
    
    content += serving_code
    
    # Écrire le nouveau contenu
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Configuration MEDIA ajoutée à urls.py")
    return True

def create_media_folders():
    """Crée les dossiers media nécessaires"""
    folders = [
        'media',
        'media/contenus',
        'media/previews',
        'media/solutions',
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ Dossier créé : {folder}/")
    
    return True

def main():
    """Fonction principale"""
    print("=" * 50)
    print("🚀 Configuration automatique de MEDIA pour Django")
    print("=" * 50)
    print()
    
    # Vérifier qu'on est dans le bon dossier
    if not os.path.exists('manage.py'):
        print("❌ Erreur : manage.py introuvable !")
        print("ℹ️  Lancez ce script depuis la racine du projet Django")
        sys.exit(1)
    
    print("📍 Dossier de travail :", os.getcwd())
    print()
    
    # Configuration de settings.py
    print("1️⃣  Configuration de settings.py...")
    if not configure_settings():
        print("❌ Échec de la configuration de settings.py")
        sys.exit(1)
    print()
    
    # Configuration de urls.py
    print("2️⃣  Configuration de urls.py...")
    if not configure_urls():
        print("❌ Échec de la configuration de urls.py")
        sys.exit(1)
    print()
    
    # Création des dossiers media
    print("3️⃣  Création des dossiers media...")
    if not create_media_folders():
        print("❌ Échec de la création des dossiers")
        sys.exit(1)
    print()
    
    # Vérification
    print("=" * 50)
    print("✅ Configuration MEDIA terminée avec succès !")
    print("=" * 50)
    print()
    print("📋 Prochaines étapes :")
    print("1. Vérifier les modifications dans settings.py et urls.py")
    print("2. Relancer le serveur : python manage.py runserver")
    print("3. Tester l'upload de fichiers")
    print()
    print("💾 Des sauvegardes ont été créées :")
    print("   - settings.py.backup")
    print("   - urls.py.backup")
    print()
    print("🎉 Vous pouvez maintenant uploader des fichiers !")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Script interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
