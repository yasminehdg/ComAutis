from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm
from .models import UserProfile, Enfant, Badge, UserBadge, Notification
from datetime import datetime
from django.urls import path
from . import views

def index(request):
    return render(request, 'authen/index.html')

def register(request):
    if request.method == "POST":
        # Récupérer les données du formulaire
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_type = request.POST.get('user_type')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        institution = request.POST.get('institution', '')
        educator_code = request.POST.get('educator_code', '')
        
        # Vérifications de base
        if password != confirm_password:
            error = "Les mots de passe ne correspondent pas"
            return render(request, 'authen/register.html', {'error': error})
        
        if User.objects.filter(username=username).exists():
            error = "Ce nom d'utilisateur existe déjà"
            return render(request, 'authen/register.html', {'error': error})
        
        if User.objects.filter(email=email).exists():
            error = "Cet email est déjà utilisé"
            return render(request, 'authen/register.html', {'error': error})
        
        # VÉRIFICATION SPÉCIALE POUR LES ÉDUCATEURS
        if user_type == 'educator':
            # Code secret pour les éducateurs (à changer en production)
            EDUCATOR_SECRET_CODE = "COMAUTISTE2024"
            
            if educator_code != EDUCATOR_SECRET_CODE:
                error = "❌ Code d'accès éducateur incorrect. Contactez l'administration."
                return render(request, 'authen/register.html', {'error': error})
            
            if not institution:
                error = "L'établissement est obligatoire pour les éducateurs"
                return render(request, 'authen/register.html', {'error': error})
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fullname
        )
        
        # Pour les éducateurs, compte INACTIF par défaut (validation admin requise)
        if user_type == 'educator':
            user.is_active = False  # Compte désactivé jusqu'à validation
            user.save()
        
        # Créer le profil utilisateur avec les infos supplémentaires
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone,
            institution=institution
        )
        
        # Attribuer le badge "Nouveau Parent" automatiquement
        if user_type == 'parent':
            from authen.badge_manager import check_and_award_badges
            check_and_award_badges(user)
        
        # Redirection selon le type
        if user_type == 'educator':
            # Message de validation en attente pour éducateur
            return render(request, 'authen/educator_pending.html', {
                'username': username,
                'email': email
            })
        else:
            # Connecter automatiquement les parents
            login(request, user)
            return redirect('dashboard')
    
    return render(request, 'authen/register.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Vérifier si le compte est actif
            if not user.is_active:
                error = "⏳ Votre compte éducateur est en attente de validation. Vous recevrez un email une fois validé."
                return render(request, 'authen/login.html', {'error': error})
            
            login(request, user)
            return redirect('dashboard')
        else:
            error = "❌ Nom d'utilisateur ou mot de passe incorrect"
            return render(request, 'authen/login.html', {'error': error})
    
    return render(request, 'authen/login.html')


def logout_view(request):
    # ✅ Accepter GET ET POST
    logout(request)
    messages.success(request, "✅ Vous avez été déconnecté avec succès !")
    return redirect('index')


@login_required
def dashboard(request):
    # ✅ REDIRECTION AUTOMATIQUE POUR LES ADMINS
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    
    # Récupérer le profil de l'utilisateur
    try:
        user_profile = request.user.profile
        user_type = user_profile.user_type
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
        user_type = 'parent'
    
    # Récupérer les notifications non lues
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # ✅ NOUVEAU : Récupérer les enfants avec leurs stats
    enfants = Enfant.objects.filter(parent=request.user)
    
    # Calculer les stats pour chaque enfant
    from .activity_tracker import get_enfant_stats, get_activites_par_jour
    enfants_avec_stats = []
    
    for enfant in enfants:
        stats = get_enfant_stats(enfant)
        activites_7jours = get_activites_par_jour(enfant, jours=7)
        
        enfants_avec_stats.append({
            'enfant': enfant,
            'stats': stats,
            'graphique_data': activites_7jours,
        })
    
    # Rediriger vers le bon dashboard selon le type
    if user_type == 'educator':
        return render(request, 'authen/dashboard_educator.html', {
            'user': request.user,
            'profile': user_profile,
            'unread_notifications': unread_notifications
        })
    else:  # parent
        return render(request, 'authen/dashboard_parent.html', {
            'user': request.user,
            'profile': user_profile,
            'unread_notifications': unread_notifications,
            'enfants_avec_stats': enfants_avec_stats,  # ✅ Nouvelles données
        })
    
@login_required
def profil_famille(request):
    # Récupérer le profil de l'utilisateur
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
    
    # Récupérer tous les enfants de l'utilisateur
    enfants = Enfant.objects.filter(parent=request.user)
    
    context = {
        'user': request.user,
        'profile': user_profile,
        'enfants': enfants,
    }
    
    return render(request, 'authen/profil_famille.html', context)


@login_required
def ajouter_enfant(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        date_naissance = request.POST.get('date_naissance')
        genre = request.POST.get('genre')
        niveau_autonomie = request.POST.get('niveau_autonomie')
        besoins_specifiques = request.POST.get('besoins_specifiques', '')
        couleur_preferee = request.POST.get('couleur_preferee', '')
        activites_preferees = request.POST.get('activites_preferees', '')
        
        # Créer l'enfant
        Enfant.objects.create(
            parent=request.user,
            prenom=prenom,
            nom=nom,
            date_naissance=date_naissance,
            genre=genre,
            niveau_autonomie=niveau_autonomie,
            besoins_specifiques=besoins_specifiques,
            couleur_preferee=couleur_preferee,
            activites_preferees=activites_preferees
        )
        
        return redirect('profil_famille')
    
    return render(request, 'authen/ajouter_enfant.html')


@login_required
def modifier_enfant(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    if request.method == 'POST':
        # Mettre à jour les informations
        enfant.prenom = request.POST.get('prenom')
        enfant.nom = request.POST.get('nom')
        enfant.date_naissance = request.POST.get('date_naissance')
        enfant.genre = request.POST.get('genre')
        enfant.niveau_autonomie = request.POST.get('niveau_autonomie')
        enfant.besoins_specifiques = request.POST.get('besoins_specifiques', '')
        enfant.couleur_preferee = request.POST.get('couleur_preferee', '')
        enfant.activites_preferees = request.POST.get('activites_preferees', '')
        enfant.save()
        
        return redirect('profil_famille')
    
    context = {
        'enfant': enfant
    }
    
    return render(request, 'authen/modifier_enfant.html', context)


@login_required
def supprimer_enfant(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    if request.method == 'POST':
        enfant.delete()
        return redirect('profil_famille')
    
    context = {
        'enfant': enfant
    }
    
    return render(request, 'authen/supprimer_enfant.html', context)


@login_required
def selection_enfant(request):
    """Page de sélection de l'enfant qui veut jouer"""
    # Récupérer tous les enfants de l'utilisateur
    enfants = Enfant.objects.filter(parent=request.user)
    
    context = {
        'enfants': enfants,
        'user': request.user,
    }
    
    return render(request, 'authen/selection_enfant.html', context)


@login_required
def dashboard_enfant(request, enfant_id):
    """Dashboard personnalisé pour l'enfant"""
    # Récupérer l'enfant (vérifier qu'il appartient bien au parent connecté)
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    context = {
        'enfant': enfant,
        'user': request.user,
    }
    
    return render(request, 'authen/dashboard_enfant.html', context)


@login_required
def jeux_enfant(request, enfant_id):
    """Page de sélection des jeux pour un enfant"""
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    context = {
        'enfant': enfant,
    }
    
    return render(request, 'authen/jeux_enfant.html', context)


@login_required
def users_list(request):
    # Récupérer tous les utilisateurs
    all_users = User.objects.all().order_by('-date_joined')
    
    # Compter les utilisateurs
    total_users = all_users.count()
    
    context = {
        'users': all_users,
        'total_users': total_users,
    }
    return render(request, 'authen/users_list.html', context)


@login_required
def liste_jeux(request):
    """Page listant tous les jeux disponibles"""
    return render(request, 'authen/jeux/liste_jeux.html')


@login_required
def jeu_memory(request):
    """Jeu Memory"""
    return render(request, 'authen/jeux/memory.html')


@login_required
def jeu_compter_3(request):
    """Jeu pour apprendre à compter jusqu'à 3"""
    return render(request, 'authen/jeux/compter_3.html')


@login_required
def jeu_couleurs(request):
    """Jeu pour apprendre les couleurs"""
    return render(request, 'authen/jeux/couleurs.html')

@login_required
def jeu_emotions(request):
    """Jeu pour apprendre les émotions"""
    return render(request, 'authen/jeux/emotions.html')

@login_required
def jeu_compter_10(request):
    """Jeu pour apprendre à compter jusqu'à 10"""
    return render(request, 'authen/jeux/compter_10.html')

@login_required
def jeu_memory_fruits(request):
    """Jeu Memory Fruits"""
    return render(request, 'authen/jeux/memory_fruits.html')

@login_required
def jeu_jours_semaine(request):
    """Jeu Jours de la Semaine"""
    return render(request, 'authen/jeux/jours_semaine.html')

@login_required
def animaux_jeu(request):
    """Jeu pour apprendre les cris des animaux"""
    # Pas besoin d'enfant_id ici
    return render(request, 'authen/jeux/animaux_jeu.html')

@login_required
def jeu_fruits(request):
    """Jeu pour apprendre les fruits"""
    return render(request, 'authen/jeux/fruits.html')

@login_required
def jeu_memory_couleurs(request):
    """Jeu Memory Couleurs"""
    return render(request, 'authen/jeux/memory_couleurs.html')

@login_required
def jeu_saisons(request):
    """Jeu pour apprendre les saisons"""
    return render(request, 'authen/jeux/saisons.html')

@login_required
def jeu_puzzle(request):
    """Jeu Puzzle"""
    return render(request, 'authen/jeux/puzzle.html')


@login_required
def page_sons(request):
    """Page des sons"""
    return render(request, 'authen/sons.html')

def pictogrammes_view(request, enfant_id):
    enfant = Enfant.objects.get(id=enfant_id)
    
    context = {
        'enfant': enfant,
    }
    
    return render(request, 'authen/pictogrammes.html', context)

def dessiner_view(request, enfant_id):
    enfant = Enfant.objects.get(id=enfant_id)
    context = {'enfant': enfant}
    return render(request, 'authen/dessiner.html', context)

def videos_view(request, enfant_id):
    enfant = Enfant.objects.get(id=enfant_id)
    context = {'enfant': enfant}
    return render(request, 'authen/videos.html', context)

def histoires_view(request, enfant_id):
    enfant = Enfant.objects.get(id=enfant_id)
    context = {'enfant': enfant}
    return render(request, 'authen/histoires.html', context)

# Vue pour la page Ressources
def ressources(request):
    return render(request, 'authen/ressources.html', {
        'user': request.user
    })

def parametres(request):
    # Récupérer les enfants de l'utilisateur connecté
    enfants = Enfant.objects.filter(parent=request.user)
    
    return render(request, 'authen/parametres.html', {
        'user': request.user,
        'enfants': enfants
    })

def labyrinthe_jeu(request):
    return render(request, 'authen/jeux/labyrinthe.html')


# ========== VUES BADGES ET NOTIFICATIONS ==========

@login_required
def user_profile(request, username):
    """Profil public d'un utilisateur avec ses badges"""
    profile_user = get_object_or_404(User, username=username)
    user_badges = UserBadge.objects.filter(user=profile_user).select_related('badge')
    
    # Statistiques
    from forum.models import Topic, Post
    topic_count = Topic.objects.filter(created_by=profile_user).count()
    post_count = Post.objects.filter(created_by=profile_user).count()
    
    context = {
        'profile_user': profile_user,
        'user_badges': user_badges,
        'topic_count': topic_count,
        'post_count': post_count,
        'total_posts': topic_count + post_count,
    }
    
    return render(request, 'authen/user_profile.html', context)


@login_required
def notifications_list(request):
    """Liste des notifications de l'utilisateur"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    # Marquer toutes les notifications comme lues
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'authen/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Rediriger vers le lien de la notification si présent
    if notification.link:
        return redirect(notification.link)
    else:
        return redirect('notifications')
    

@login_required
def progression(request):
    """Page de suivi de progression des enfants"""
    # Récupérer tous les enfants de l'utilisateur
    enfants = Enfant.objects.filter(parent=request.user)
    
    # Calculer les stats pour chaque enfant
    from .activity_tracker import get_enfant_stats, get_activites_par_jour
    import json
    
    enfants_avec_stats = []
    
    for enfant in enfants:
        stats = get_enfant_stats(enfant)
        activites_7jours = get_activites_par_jour(enfant, jours=7)
        
        # Convertir les données pour le graphique en JSON
        graphique_json = json.dumps(activites_7jours, default=str)
        
        enfants_avec_stats.append({
            'enfant': enfant,
            'stats': stats,
            'graphique_data': graphique_json,
        })
    
    context = {
        'user': request.user,
        'enfants_avec_stats': enfants_avec_stats,
    }
    
    return render(request, 'authen/progression.html', context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
from django.utils import timezone
import json

@login_required
def progression_view(request):
    """Vue pour afficher la progression de tous les enfants"""
    
    # Récupérer tous les enfants du parent connecté
    enfants = request.user.enfants.all()  # Ajuste selon ton modèle
    
    enfants_avec_stats = []
    
    for enfant in enfants:
        # Calculer les stats pour cet enfant
        stats = calculer_stats_enfant(enfant)
        
        # Données pour le graphique des 7 derniers jours
        graphique_data = generer_graphique_7_jours(enfant)
        
        enfants_avec_stats.append({
            'enfant': enfant,
            'stats': stats,
            'graphique_data': json.dumps(graphique_data)
        })
    
    context = {
        'enfants_avec_stats': enfants_avec_stats,
    }
    
    return render(request, 'progression.html', context)


def calculer_stats_enfant(enfant):
    """Calcule toutes les stats pour un enfant"""
    from datetime import date
    
    # Importe ton modèle Activite
    from .models import Activite  # Ajuste selon ton app
    
    aujourd_hui = date.today()
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    
    # Activités d'aujourd'hui
    activites_today = Activite.objects.filter(
        enfant=enfant,
        date_debut__date=aujourd_hui
    ).count()
    
    # Activités de la semaine
    activites_week = Activite.objects.filter(
        enfant=enfant,
        date_debut__date__gte=debut_semaine
    ).count()
    
    # Temps passé aujourd'hui (en minutes)
    activites_jour = Activite.objects.filter(
        enfant=enfant,
        date_debut__date=aujourd_hui,
        date_fin__isnull=False
    )
    
    temps_total = 0
    for act in activites_jour:
        if act.date_fin:
            duree = (act.date_fin - act.date_debut).total_seconds() / 60
            temps_total += duree
    
    temps_aujourd_hui_minutes = int(temps_total)
    
    # Taux de réussite
    activites_terminees = Activite.objects.filter(
        enfant=enfant,
        date_fin__isnull=False
    )
    
    if activites_terminees.exists():
        reussies = activites_terminees.filter(reussi=True).count()
        total = activites_terminees.count()
        taux_reussite = int((reussies / total) * 100) if total > 0 else 0
    else:
        taux_reussite = 0
    
    # Streak (jours consécutifs)
    streak_jours = calculer_streak(enfant)
    
    # Jeux favoris (top 3)
    jeux_favoris = Activite.objects.filter(
        enfant=enfant
    ).values('jeu').annotate(
        count=Count('id')
    ).order_by('-count')[:3]
    
    # Convertir les noms de jeux en français
    jeux_favoris_liste = []
    noms_jeux = {
        'memory': 'Memory',
        'compter_3': 'Compter jusqu\'à 3',
        'compter_10': 'Compter jusqu\'à 10',
        'couleurs': 'Les Couleurs',
        'emotions': 'Les Émotions',
        'animaux': 'Les Animaux',
        'fruits': 'Les Fruits',
        'puzzle': 'Puzzle',
        'labyrinthe': 'Labyrinthe',
    }
    
    for jeu in jeux_favoris:
        jeux_favoris_liste.append({
            'jeu': noms_jeux.get(jeu['jeu'], jeu['jeu']),
            'count': jeu['count']
        })
    
    return {
        'activites_today': activites_today,
        'activites_week': activites_week,
        'temps_aujourd_hui_minutes': temps_aujourd_hui_minutes,
        'taux_reussite': taux_reussite,
        'streak_jours': streak_jours,
        'jeux_favoris': jeux_favoris_liste,
    }


def calculer_streak(enfant):
    """Calcule le nombre de jours consécutifs où l'enfant a joué"""
    from datetime import date, timedelta
    from .models import Activite
    
    aujourd_hui = date.today()
    streak = 0
    jour_actuel = aujourd_hui
    
    # Vérifier les jours en remontant dans le temps
    while True:
        activites_jour = Activite.objects.filter(
            enfant=enfant,
            date_debut__date=jour_actuel
        ).exists()
        
        if activites_jour:
            streak += 1
            jour_actuel -= timedelta(days=1)
        else:
            break
        
        # Limite de sécurité
        if streak > 365:
            break
    
    return streak


def generer_graphique_7_jours(enfant):
    """Génère les données pour le graphique des 7 derniers jours"""
    from datetime import date, timedelta
    from .models import Activite
    
    data = []
    aujourd_hui = date.today()
    
    jours_semaine = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    
    for i in range(6, -1, -1):  # De -6 à 0
        jour = aujourd_hui - timedelta(days=i)
        
        # Compter les activités de ce jour
        count = Activite.objects.filter(
            enfant=enfant,
            date_debut__date=jour
        ).count()
        
        # Nom du jour
        jour_nom = jours_semaine[jour.weekday()]
        
        data.append({
            'jour': jour_nom,
            'count': count
        })
    
    return data


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

# ===========================
# VUE PRINCIPALE PARAMÈTRES
# ===========================
@login_required
def parametres_view(request):
    """Page principale des paramètres"""
    
    # Récupérer les enfants du parent
    enfants = request.user.enfants.all()  # Ajuste selon ton modèle
    
    # Récupérer ou créer les préférences utilisateur
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    context = {
        'enfants': enfants,
        'preferences': preferences,
    }
    
    return render(request, 'parametres.html', context)


# ===========================
# MODIFIER LE PROFIL
# ===========================
@login_required
@require_POST
def modifier_profil(request):
    """Modifier nom, prénom, email"""
    
    data = json.loads(request.body)
    user = request.user
    
    # Mettre à jour les informations
    if 'first_name' in data:
        user.first_name = data['first_name']
    
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    if 'email' in data:
        # Vérifier que l'email n'existe pas déjà
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
            return JsonResponse({
                'success': False,
                'message': 'Cet email est déjà utilisé'
            })
        
        user.email = data['email']
    
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Profil mis à jour avec succès !'
    })


# ===========================
# CHANGER LE MOT DE PASSE
# ===========================
@login_required
@require_POST
def changer_mot_de_passe(request):
    """Changer le mot de passe"""
    
    data = json.loads(request.body)
    user = request.user
    
    ancien_mdp = data.get('ancien_mdp')
    nouveau_mdp = data.get('nouveau_mdp')
    confirmer_mdp = data.get('confirmer_mdp')
    
    # Vérifier l'ancien mot de passe
    if not user.check_password(ancien_mdp):
        return JsonResponse({
            'success': False,
            'message': 'Mot de passe actuel incorrect'
        })
    
    # Vérifier que les nouveaux mots de passe correspondent
    if nouveau_mdp != confirmer_mdp:
        return JsonResponse({
            'success': False,
            'message': 'Les mots de passe ne correspondent pas'
        })
    
    # Vérifier la longueur
    if len(nouveau_mdp) < 8:
        return JsonResponse({
            'success': False,
            'message': 'Le mot de passe doit contenir au moins 8 caractères'
        })
    
    # Changer le mot de passe
    user.set_password(nouveau_mdp)
    user.save()
    
    # Garder l'utilisateur connecté
    update_session_auth_hash(request, user)
    
    return JsonResponse({
        'success': True,
        'message': 'Mot de passe changé avec succès !'
    })


# ===========================
# UPLOAD PHOTO DE PROFIL
# ===========================
@login_required
@require_POST
def upload_photo_profil(request):
    """Upload de la photo de profil"""
    
    if 'photo' not in request.FILES:
        return JsonResponse({
            'success': False,
            'message': 'Aucune photo fournie'
        })
    
    photo = request.FILES['photo']
    
    # Vérifier la taille (max 5MB)
    if photo.size > 5 * 1024 * 1024:
        return JsonResponse({
            'success': False,
            'message': 'La photo est trop volumineuse (max 5MB)'
        })
    
    # Vérifier le type
    if not photo.content_type.startswith('image/'):
        return JsonResponse({
            'success': False,
            'message': 'Le fichier doit être une image'
        })
    
    # Sauvegarder la photo
    user = request.user
    user.photo_profil = photo  # Assure-toi d'avoir ce champ dans ton modèle User
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Photo de profil mise à jour !',
        'photo_url': user.photo_profil.url if user.photo_profil else None
    })


# ===========================
# SUPPRIMER UN ENFANT
# ===========================
@login_required
@require_POST
def supprimer_enfant(request, enfant_id):
    """Supprimer un enfant"""
    
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    prenom = enfant.prenom
    enfant.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Le profil de {prenom} a été supprimé'
    })


# ===========================
# METTRE À JOUR LES PRÉFÉRENCES
# ===========================
@login_required
@require_POST
def update_preferences(request):
    """Mettre à jour toutes les préférences"""
    
    data = json.loads(request.body)
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    # Notifications
    if 'notifications_email' in data:
        preferences.notifications_email = data['notifications_email']
    
    if 'rappels_routine' in data:
        preferences.rappels_routine = data['rappels_routine']
    
    if 'alertes_forum' in data:
        preferences.alertes_forum = data['alertes_forum']
    
    if 'newsletter' in data:
        preferences.newsletter = data['newsletter']
    
    # Affichage
    if 'theme' in data:
        preferences.theme = data['theme']
    
    if 'taille_police' in data:
        preferences.taille_police = data['taille_police']
    
    if 'langue' in data:
        preferences.langue = data['langue']
    
    if 'contraste_eleve' in data:
        preferences.contraste_eleve = data['contraste_eleve']
    
    # Sons
    if 'sons_jeux' in data:
        preferences.sons_jeux = data['sons_jeux']
    
    if 'musique_fond' in data:
        preferences.musique_fond = data['musique_fond']
    
    if 'volume' in data:
        preferences.volume = data['volume']
    
    if 'lecture_vocale' in data:
        preferences.lecture_vocale = data['lecture_vocale']
    
    # Confidentialité
    if 'visibilite_profil' in data:
        preferences.visibilite_profil = data['visibilite_profil']
    
    if 'partage_donnees' in data:
        preferences.partage_donnees = data['partage_donnees']
    
    preferences.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Préférences enregistrées avec succès !'
    })


# ===========================
# SUPPRIMER LE COMPTE
# ===========================
@login_required
@require_POST
def supprimer_compte(request):
    """Supprimer définitivement le compte"""
    
    data = json.loads(request.body)
    mot_de_passe = data.get('mot_de_passe')
    
    # Vérifier le mot de passe
    if not request.user.check_password(mot_de_passe):
        return JsonResponse({
            'success': False,
            'message': 'Mot de passe incorrect'
        })
    
    # Supprimer le compte
    user = request.user
    user.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Compte supprimé avec succès',
        'redirect': '/goodbye/'  # Page de confirmation
    })


# ===========================
# MODÈLE USER PREFERENCES
# ===========================
from django.db import models
from django.contrib.auth.models import User

class UserPreferences(models.Model):
    """Modèle pour stocker les préférences utilisateur"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notifications
    notifications_email = models.BooleanField(default=True)
    rappels_routine = models.BooleanField(default=True)
    alertes_forum = models.BooleanField(default=False)
    newsletter = models.BooleanField(default=True)
    
    # Affichage
    THEME_CHOICES = [
        ('clair', 'Mode clair'),
        ('sombre', 'Mode sombre'),
        ('auto', 'Automatique'),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='clair')
    
    TAILLE_CHOICES = [
        ('petite', 'Petite'),
        ('normale', 'Normale'),
        ('grande', 'Grande'),
        ('tres_grande', 'Très grande'),
    ]
    taille_police = models.CharField(max_length=15, choices=TAILLE_CHOICES, default='normale')
    
    LANGUE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
    ]
    langue = models.CharField(max_length=5, choices=LANGUE_CHOICES, default='fr')
    
    contraste_eleve = models.BooleanField(default=False)
    
    # Sons
    sons_jeux = models.BooleanField(default=True)
    musique_fond = models.BooleanField(default=False)
    
    VOLUME_CHOICES = [
        ('silencieux', 'Silencieux'),
        ('faible', 'Faible'),
        ('moyen', 'Moyen'),
        ('fort', 'Fort'),
    ]
    volume = models.CharField(max_length=15, choices=VOLUME_CHOICES, default='moyen')
    
    lecture_vocale = models.BooleanField(default=False)
    
    # Confidentialité
    VISIBILITE_CHOICES = [
        ('tous', 'Tous les membres'),
        ('amis', 'Amis uniquement'),
        ('prive', 'Privé'),
    ]
    visibilite_profil = models.CharField(max_length=10, choices=VISIBILITE_CHOICES, default='tous')
    
    partage_donnees = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Préférences de {self.user.username}"
    
    class Meta:
        verbose_name = "Préférence utilisateur"
        verbose_name_plural = "Préférences utilisateur"


