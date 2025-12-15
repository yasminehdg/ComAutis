from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils import timezone
import json

from .forms import RegisterForm
from .models import (
    UserProfile, Enfant, Badge, UserBadge, Notification, 
    Activite, EducateurEnfant, ObservationEducateur
)


# ==========================================
# 🎮 FONCTION HELPER UNIVERSELLE POUR JEUX
# ==========================================
def render_jeu_avec_tracking(request, enfant_id, template_name):
    """
    Fonction universelle qui gère TOUS les jeux avec tracking automatique
    Vérifie que l'enfant appartient bien au parent connecté
    """
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    context = {
        'enfant': enfant,
        'user': request.user,
    }
    
    return render(request, template_name, context)


# ==========================================
# PAGES PRINCIPALES
# ==========================================
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


# ==========================================
# ✨ DASHBOARD INTELLIGENT (AVEC ÉDUCATEURS)
# ==========================================
@login_required
def dashboard(request):
    """Dashboard intelligent selon le type d'utilisateur"""
    
    # Redirection admin
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    
    # Récupérer le profil
    try:
        user_profile = request.user.profile
        user_type = user_profile.user_type
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
        user_type = 'parent'
    
    # Notifications non lues
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # ==========================================
    # 👨‍🏫 DASHBOARD ÉDUCATEUR
    # ==========================================
    if user_type == 'educator':
        # Récupérer les enfants suivis
        relations = EducateurEnfant.objects.filter(
            educateur=request.user,
            statut='actif'
        ).select_related('enfant', 'enfant__parent')
        
        # Stats globales
        total_enfants = relations.count()
        
        # Calculer les stats pour chaque enfant
        enfants_avec_stats = []
        total_activites_semaine = 0
        total_temps_minutes = 0
        total_reussite_sum = 0
        
        for relation in relations:
            enfant = relation.enfant
            
            # Stats de la semaine
            debut_semaine = timezone.now() - timedelta(days=7)
            activites_semaine = Activite.objects.filter(
                enfant=enfant,
                date_debut__gte=debut_semaine
            )
            
            nb_activites = activites_semaine.count()
            total_activites_semaine += nb_activites
            
            # Calcul du temps passé sécurisé
            temps_minutes = 0
            for act in activites_semaine:
                if act.duree_minutes and act.duree_minutes > 0:
                    temps_minutes += act.duree_minutes
                elif act.date_fin and act.date_fin > act.date_debut:
                    duree = (act.date_fin - act.date_debut).total_seconds() / 60
                    if duree > 0 and duree < 1440:
                        temps_minutes += duree
            
            total_temps_minutes += temps_minutes
            
            # Taux de réussite
            activites_terminees = activites_semaine.filter(date_fin__isnull=False)
            if activites_terminees.exists():
                reussies = activites_terminees.filter(reussi=True).count()
                total = activites_terminees.count()
                taux_reussite = int((reussies / total) * 100)
            else:
                taux_reussite = 0
            
            total_reussite_sum += taux_reussite
            
            enfants_avec_stats.append({
                'relation': relation,
                'enfant': enfant,
                'nb_activites': nb_activites,
                'temps_minutes': int(temps_minutes),
                'taux_reussite': taux_reussite,
            })
        
        # Moyennes sécurisées
        taux_moyen = int(total_reussite_sum / total_enfants) if total_enfants > 0 else 0
        total_temps_heures = int(total_temps_minutes / 60) if total_temps_minutes > 0 else 0
        
        # Activités récentes (toutes confondues)
        activites_recentes = Activite.objects.filter(
            enfant__educateurs__educateur=request.user,
            enfant__educateurs__statut='actif'
        ).select_related('enfant').order_by('-date_debut')[:8]
        
        context = {
            'user': request.user,
            'profile': user_profile,
            'unread_notifications': unread_notifications,
            'total_enfants': total_enfants,
            'total_activites_semaine': total_activites_semaine,
            'total_temps_heures': total_temps_heures,
            'taux_moyen': taux_moyen,
            'enfants_avec_stats': enfants_avec_stats,
            'activites_recentes': activites_recentes,
        }
        
        return render(request, 'authen/dashboard_educator.html', context)
    
    # ==========================================
    # 👨‍👩‍👧 DASHBOARD PARENT
    # ==========================================
    else:
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
        
        return render(request, 'authen/dashboard_parent.html', {
            'user': request.user,
            'profile': user_profile,
            'unread_notifications': unread_notifications,
            'enfants_avec_stats': enfants_avec_stats,
        })


# ==========================================
# ✨ DÉTAIL D'UN ENFANT POUR L'ÉDUCATEUR
# ==========================================
@login_required
def educateur_enfant_detail(request, enfant_id):
    """Page de détail d'un enfant pour l'éducateur"""
    
    if request.user.profile.user_type != 'educator':
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
    
    enfant = get_object_or_404(Enfant, id=enfant_id)
    relation = get_object_or_404(EducateurEnfant, educateur=request.user, enfant=enfant, statut='actif')
    
    # Stats détaillées
    activites = Activite.objects.filter(enfant=enfant).order_by('-date_debut')[:20]
    
    total_activites = Activite.objects.filter(enfant=enfant).count()
    activites_semaine = Activite.objects.filter(
        enfant=enfant,
        date_debut__gte=datetime.now() - timedelta(days=7)
    ).count()
    
    # Taux de réussite global
    activites_terminees = Activite.objects.filter(enfant=enfant, date_fin__isnull=False)
    if activites_terminees.exists():
        reussies = activites_terminees.filter(reussi=True).count()
        taux_reussite = int((reussies / activites_terminees.count()) * 100)
    else:
        taux_reussite = 0
    
    # Jeux favoris
    jeux_favoris = Activite.objects.filter(enfant=enfant).values('jeu').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Observations de cet éducateur
    observations = ObservationEducateur.objects.filter(
        educateur=request.user,
        enfant=enfant
    ).order_by('-date_observation')
    
    context = {
        'enfant': enfant,
        'relation': relation,
        'activites': activites,
        'total_activites': total_activites,
        'activites_semaine': activites_semaine,
        'taux_reussite': taux_reussite,
        'jeux_favoris': jeux_favoris,
        'observations': observations,
    }
    
    return render(request, 'authen/educateur_enfant_detail.html', context)


# ==========================================
# ✨ AJOUTER UNE OBSERVATION
# ==========================================
@login_required
def educateur_ajouter_observation(request, enfant_id):
    """Ajouter une observation sur un enfant"""
    
    if request.user.profile.user_type != 'educator':
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
    
    enfant = get_object_or_404(Enfant, id=enfant_id)
    
    if not EducateurEnfant.objects.filter(educateur=request.user, enfant=enfant, statut='actif').exists():
        messages.error(request, "Vous ne suivez pas cet enfant.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        type_observation = request.POST.get('type_observation')
        visible_parent = request.POST.get('visible_parent') == 'on'
        
        ObservationEducateur.objects.create(
            educateur=request.user,
            enfant=enfant,
            titre=titre,
            description=description,
            type_observation=type_observation,
            visible_parent=visible_parent
        )
        
        if visible_parent:
            Notification.objects.create(
                user=enfant.parent,
                notification_type='mention',
                message=f"📝 {request.user.username} a ajouté une observation sur {enfant.prenom}",
                link=f'/enfant/{enfant.id}/observations/'
            )
        
        messages.success(request, "✅ Observation ajoutée avec succès !")
        return redirect('educateur_enfant_detail', enfant_id=enfant.id)
    
    context = {
        'enfant': enfant,
    }
    
    return render(request, 'authen/educateur_ajouter_observation.html', context)


# ==========================================
# ✨ PARENT VOIR LES OBSERVATIONS
# ==========================================
@login_required
def parent_voir_observations(request, enfant_id):
    """Parent voit les observations visibles sur son enfant"""
    
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    # Récupérer les observations visibles
    observations = ObservationEducateur.objects.filter(
        enfant=enfant,
        visible_parent=True
    ).select_related('educateur').order_by('-date_observation')
    
    # Éducateurs qui suivent cet enfant
    educateurs = EducateurEnfant.objects.filter(enfant=enfant, statut='actif').select_related('educateur')
    
    context = {
        'enfant': enfant,
        'observations': observations,
        'educateurs': educateurs,
    }
    
    return render(request, 'authen/parent_observations.html', context)


# ==========================================
# GESTION FAMILLE
# ==========================================
@login_required
def profil_famille(request):
    """Profil famille avec compteur d'observations"""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
    
    # Récupérer les enfants
    enfants = Enfant.objects.filter(parent=request.user)
    
    # Ajouter le nombre d'observations visibles pour chaque enfant
    enfants_avec_obs = []
    for enfant in enfants:
        nb_observations = ObservationEducateur.objects.filter(
            enfant=enfant,
            visible_parent=True
        ).count()
        
        enfant.nb_observations = nb_observations
        enfants_avec_obs.append(enfant)
    
    context = {
        'user': request.user,
        'profile': user_profile,
        'enfants': enfants_avec_obs,
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
    
    context = {'enfant': enfant}
    return render(request, 'authen/modifier_enfant.html', context)


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
def users_list(request):
    all_users = User.objects.all().order_by('-date_joined')
    total_users = all_users.count()
    
    context = {
        'users': all_users,
        'total_users': total_users,
    }
    return render(request, 'authen/users_list.html', context)


# ==========================================
# 🎮 JEUX AVEC TRACKING AUTOMATIQUE
# ==========================================
@login_required
def liste_jeux(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/liste_jeux.html')

@login_required
def jeu_memory(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/memory.html')

@login_required
def jeu_compter_3(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/compter_3.html')

@login_required
def jeu_couleurs(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/couleurs.html')

@login_required
def jeu_emotions(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/emotions.html')

@login_required
def jeu_compter_10(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/compter_10.html')

@login_required
def jeu_memory_fruits(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/memory_fruits.html')

@login_required
def jeu_jours_semaine(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/jours_semaine.html')

@login_required
def animaux_jeu(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/animaux_jeu.html')

@login_required
def jeu_fruits(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/fruits.html')

@login_required
def jeu_memory_couleurs(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/memory_couleurs.html')

@login_required
def jeu_saisons(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/saisons.html')

@login_required
def jeu_puzzle(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/puzzle.html')

@login_required
def labyrinthe_jeu(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/jeux/labyrinthe.html')


# ==========================================
# ACTIVITÉS ENFANT (AVEC TRACKING)
# ==========================================
@login_required
def page_sons(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/sons.html')

@login_required
def pictogrammes_view(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/pictogrammes.html')

@login_required
def dessiner_view(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/dessiner.html')

@login_required
def videos_view(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/videos.html')

@login_required
def histoires_view(request, enfant_id):
    return render_jeu_avec_tracking(request, enfant_id, 'authen/histoires.html')


# ==========================================
# RESSOURCES ET PARAMÈTRES
# ==========================================
@login_required
def ressources(request):
    return render(request, 'authen/ressources.html', {'user': request.user})

@login_required
def parametres(request):
    enfants = Enfant.objects.filter(parent=request.user)
    return render(request, 'authen/parametres.html', {
        'user': request.user,
        'enfants': enfants
    })

@login_required
def progression(request):
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
    
    context = {
        'user': request.user,
        'enfants_avec_stats': enfants_avec_stats,
    }
    
    return render(request, 'authen/progression.html', context)


# ==========================================
# BADGES ET NOTIFICATIONS
# ==========================================
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
    
    context = {'notifications': notifications}
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


# ==========================================
# API ENDPOINTS
# ==========================================
@login_required
@require_POST
def modifier_profil(request):
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


@login_required
@require_POST
def changer_mot_de_passe(request):
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


@login_required
@require_POST
def upload_photo_profil(request):
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
    
    user = request.user
    user.photo_profil = photo
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Photo de profil mise à jour !',
        'photo_url': user.photo_profil.url if user.photo_profil else None
    })


@login_required
@require_POST
def supprimer_enfant(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    prenom = enfant.prenom
    enfant.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Le profil de {prenom} a été supprimé'
    })


@login_required
@require_POST
def supprimer_compte(request):
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
        'redirect': '/goodbye/'
    })


# ==========================================
# 🎮 API TRACKING ACTIVITÉS
# ==========================================
@csrf_exempt
def start_activity_api(request):
    """API pour démarrer une activité automatiquement"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            enfant_id = data.get('enfant_id')
            jeu = data.get('jeu')
            
            if not enfant_id or not jeu:
                return JsonResponse({'success': False, 'error': 'Missing data'})
            
            enfant = Enfant.objects.get(id=enfant_id)
            
            # Créer l'activité
            activite = Activite.objects.create(
                enfant=enfant,
                jeu=jeu,
                date_debut=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'activite_id': activite.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@csrf_exempt
def end_activity_api(request):
    """API pour terminer une activité automatiquement"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            activite_id = data.get('activite_id')
            score = data.get('score', 50)
            reussi = data.get('reussi', True)
            
            if not activite_id:
                return JsonResponse({'success': False, 'error': 'Missing activite_id'})
            
            activite = Activite.objects.get(id=activite_id)
            activite.date_fin = timezone.now()
            activite.score = score
            activite.reussi = reussi
            activite.calculer_duree()
            
            return JsonResponse({
                'success': True,
                'duree_minutes': activite.duree_minutes
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})