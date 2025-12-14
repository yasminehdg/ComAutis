from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count
from datetime import datetime, timedelta, date
from django.utils import timezone
import json

from .forms import RegisterForm
from .models import UserProfile, Enfant, Badge, UserBadge, Notification, UserPreferences, Activite


def index(request):
    return render(request, 'authen/index.html')


def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_type = request.POST.get('user_type')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        institution = request.POST.get('institution', '')
        educator_code = request.POST.get('educator_code', '')
        
        if password != confirm_password:
            error = "Les mots de passe ne correspondent pas"
            return render(request, 'authen/register.html', {'error': error})
        
        if User.objects.filter(username=username).exists():
            error = "Ce nom d'utilisateur existe déjà"
            return render(request, 'authen/register.html', {'error': error})
        
        if User.objects.filter(email=email).exists():
            error = "Cet email est déjà utilisé"
            return render(request, 'authen/register.html', {'error': error})
        
        if user_type == 'educator':
            EDUCATOR_SECRET_CODE = "COMAUTISTE2024"
            
            if educator_code != EDUCATOR_SECRET_CODE:
                error = "❌ Code d'accès éducateur incorrect. Contactez l'administration."
                return render(request, 'authen/register.html', {'error': error})
            
            if not institution:
                error = "L'établissement est obligatoire pour les éducateurs"
                return render(request, 'authen/register.html', {'error': error})
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fullname
        )
        
        if user_type == 'educator':
            user.is_active = False
            user.save()
        
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone,
            institution=institution
        )
        
        if user_type == 'parent':
            from authen.badge_manager import check_and_award_badges
            check_and_award_badges(user)
        
        if user_type == 'educator':
            return render(request, 'authen/educator_pending.html', {
                'username': username,
                'email': email
            })
        else:
            login(request, user)
            return redirect('dashboard')
    
    return render(request, 'authen/register.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
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
    logout(request)
    messages.success(request, "✅ Vous avez été déconnecté avec succès !")
    return redirect('index')


@login_required
def dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    
    try:
        user_profile = request.user.profile
        user_type = user_profile.user_type
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
        user_type = 'parent'
    
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    enfants = Enfant.objects.filter(parent=request.user)
    
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
    
    if user_type == 'educator':
        return render(request, 'authen/dashboard_educator.html', {
            'user': request.user,
            'profile': user_profile,
            'unread_notifications': unread_notifications
        })
    else:
        return render(request, 'authen/dashboard_parent.html', {
            'user': request.user,
            'profile': user_profile,
            'unread_notifications': unread_notifications,
            'enfants_avec_stats': enfants_avec_stats,
        })


@login_required
def profil_famille(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
    
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
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        date_naissance = request.POST.get('date_naissance')
        genre = request.POST.get('genre')
        niveau_autonomie = request.POST.get('niveau_autonomie')
        besoins_specifiques = request.POST.get('besoins_specifiques', '')
        couleur_preferee = request.POST.get('couleur_preferee', '')
        activites_preferees = request.POST.get('activites_preferees', '')
        
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
def supprimer_enfant_view(request, enfant_id):
    """Page de confirmation de suppression d'un enfant"""
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    if request.method == 'POST':
        enfant.delete()
        messages.success(request, f"Le profil de {enfant.prenom} a été supprimé.")
        return redirect('profil_famille')
    
    context = {
        'enfant': enfant
    }
    
    return render(request, 'authen/supprimer_enfant.html', context)


@login_required
def selection_enfant(request):
    enfants = Enfant.objects.filter(parent=request.user)
    
    context = {
        'enfants': enfants,
        'user': request.user,
    }
    
    return render(request, 'authen/selection_enfant.html', context)


@login_required
def dashboard_enfant(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    context = {
        'enfant': enfant,
        'user': request.user,
    }
    
    return render(request, 'authen/dashboard_enfant.html', context)


@login_required
def jeux_enfant(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    context = {
        'enfant': enfant,
    }
    
    return render(request, 'authen/jeux_enfant.html', context)


@login_required
def users_list(request):
    all_users = User.objects.all().order_by('-date_joined')
    total_users = all_users.count()
    
    context = {
        'users': all_users,
        'total_users': total_users,
    }
    return render(request, 'authen/users_list.html', context)


@login_required
def liste_jeux(request):
    return render(request, 'authen/jeux/liste_jeux.html')


@login_required
def jeu_memory(request):
    return render(request, 'authen/jeux/memory.html')


@login_required
def jeu_compter_3(request):
    return render(request, 'authen/jeux/compter_3.html')


@login_required
def jeu_couleurs(request):
    return render(request, 'authen/jeux/couleurs.html')


@login_required
def jeu_emotions(request):
    return render(request, 'authen/jeux/emotions.html')


@login_required
def jeu_compter_10(request):
    return render(request, 'authen/jeux/compter_10.html')


@login_required
def jeu_memory_fruits(request):
    return render(request, 'authen/jeux/memory_fruits.html')


@login_required
def jeu_jours_semaine(request):
    return render(request, 'authen/jeux/jours_semaine.html')


@login_required
def animaux_jeu(request):
    return render(request, 'authen/jeux/animaux_jeu.html')


@login_required
def jeu_fruits(request):
    return render(request, 'authen/jeux/fruits.html')


@login_required
def jeu_memory_couleurs(request):
    return render(request, 'authen/jeux/memory_couleurs.html')


@login_required
def jeu_saisons(request):
    return render(request, 'authen/jeux/saisons.html')


@login_required
def jeu_puzzle(request):
    return render(request, 'authen/jeux/puzzle.html')


@login_required
def labyrinthe_jeu(request):
    return render(request, 'authen/jeux/labyrinthe.html')


@login_required
def page_sons(request):
    return render(request, 'authen/sons.html')


def pictogrammes_view(request, enfant_id):
    enfant = Enfant.objects.get(id=enfant_id)
    context = {'enfant': enfant}
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


def ressources(request):
    return render(request, 'authen/ressources.html', {
        'user': request.user
    })


@login_required
def parametres(request):
    enfants = Enfant.objects.filter(parent=request.user)
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    return render(request, 'authen/parametres.html', {
        'user': request.user,
        'enfants': enfants,
        'preferences': preferences,
    })


@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_badges = UserBadge.objects.filter(user=profile_user).select_related('badge')
    
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
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'authen/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.link:
        return redirect(notification.link)
    else:
        return redirect('notifications')


@login_required
def progression(request):
    enfants = Enfant.objects.filter(parent=request.user)
    
    from .activity_tracker import get_enfant_stats, get_activites_par_jour
    enfants_avec_stats = []
    
    for enfant in enfants:
        stats = get_enfant_stats(enfant)
        activites_7jours = get_activites_par_jour(enfant, jours=7)
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


# ========================================
# API ENDPOINTS POUR AJAX
# ========================================

@login_required
@require_POST
def modifier_profil(request):
    """API - Modifier nom, prénom, email"""
    try:
        data = json.loads(request.body)
        user = request.user
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        if 'email' in data:
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
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur : {str(e)}'
        }, status=500)


@login_required
@require_POST
def changer_mot_de_passe(request):
    """API - Changer le mot de passe"""
    try:
        data = json.loads(request.body)
        user = request.user
        
        ancien_mdp = data.get('ancien_mdp')
        nouveau_mdp = data.get('nouveau_mdp')
        confirmer_mdp = data.get('confirmer_mdp')
        
        if not user.check_password(ancien_mdp):
            return JsonResponse({
                'success': False,
                'message': 'Mot de passe actuel incorrect'
            })
        
        if nouveau_mdp != confirmer_mdp:
            return JsonResponse({
                'success': False,
                'message': 'Les mots de passe ne correspondent pas'
            })
        
        if len(nouveau_mdp) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Le mot de passe doit contenir au moins 8 caractères'
            })
        
        user.set_password(nouveau_mdp)
        user.save()
        update_session_auth_hash(request, user)
        
        return JsonResponse({
            'success': True,
            'message': 'Mot de passe changé avec succès !'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur : {str(e)}'
        }, status=500)


@login_required
@require_POST
def upload_photo_profil(request):
    """API - Upload de la photo de profil"""
    try:
        if 'photo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'Aucune photo fournie'
            })
        
        photo = request.FILES['photo']
        
        if photo.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'message': 'La photo est trop volumineuse (max 5MB)'
            })
        
        if not photo.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'message': 'Le fichier doit être une image'
            })
        
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        
        profile.photo_profil = photo
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo de profil mise à jour !',
            'photo_url': profile.photo_profil.url if profile.photo_profil else None
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur : {str(e)}'
        }, status=500)


@login_required
@require_POST
def api_supprimer_enfant(request, enfant_id):
    """API - Supprimer un enfant"""
    try:
        enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
        prenom = enfant.prenom
        enfant.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Le profil de {prenom} a été supprimé'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur : {str(e)}'
        }, status=500)


@login_required
@require_POST
def update_preferences(request):
    """API - Mettre à jour les préférences"""
    try:
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
            'message': 'Préférences enregistrées'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur : {str(e)}'
        }, status=500)


@login_required
@require_POST
def supprimer_compte(request):
    """API - Supprimer définitivement le compte"""
    try:
        data = json.loads(request.body)
        mot_de_passe = data.get('mot_de_passe')
        
        if not request.user.check_password(mot_de_passe):
            return JsonResponse({
                'success': False,
                'message': 'Mot de passe incorrect'
            })
        
        user = request.user
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Compte supprimé avec succès',
            'redirect': '/'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur : {str(e)}'
        }, status=500)