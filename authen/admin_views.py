from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile, Enfant, Badge, UserBadge, Notification
from forum.models import Topic, Post
from paiement.models import Subscription
import json

# Fonction pour vérifier si l'utilisateur est admin
def is_admin(user):
    return user.is_staff or user.is_superuser

# Décorateur pour protéger les vues admin
def admin_required(view_func):
    decorated_view = login_required(user_passes_test(is_admin, login_url='/login/')(view_func))
    return decorated_view


# ========== DASHBOARD PRINCIPAL ==========
@admin_required
def admin_dashboard(request):
    """Dashboard principal avec statistiques"""
    
    # Statistiques utilisateurs
    total_users = User.objects.count()
    total_parents = UserProfile.objects.filter(user_type='parent').count()
    total_educators = UserProfile.objects.filter(user_type='educator').count()
    pending_educators = UserProfile.objects.filter(user_type='educator', user__is_active=False).count()
    
    # Statistiques enfants
    total_enfants = Enfant.objects.count()
    
    # Statistiques forum
    total_topics = Topic.objects.count()
    total_posts = Post.objects.count()
    
    # Statistiques abonnements
    active_subscriptions = Subscription.objects.filter(active=True).count()
    
    # Utilisateurs récents (derniers 7 jours)
    week_ago = timezone.now() - timedelta(days=7)
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    
    # Badges attribués
    total_badges = UserBadge.objects.count()
    
    # Derniers utilisateurs inscrits
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Éducateurs en attente
    pending_educator_profiles = UserProfile.objects.filter(
        user_type='educator', 
        user__is_active=False
    ).select_related('user')[:5]
    
    # Topics récents
    recent_topics = Topic.objects.order_by('-created_at')[:5]
    
    # Données pour les graphiques
    users_by_month = []
    for i in range(6, -1, -1):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = timezone.now() - timedelta(days=30*(i-1)) if i > 0 else timezone.now()
        count = User.objects.filter(date_joined__gte=month_start, date_joined__lt=month_end).count()
        users_by_month.append({
            'month': month_start.strftime('%b'),
            'count': count
        })
    
    context = {
        'total_users': total_users,
        'total_parents': total_parents,
        'total_educators': total_educators,
        'pending_educators': pending_educators,
        'total_enfants': total_enfants,
        'total_topics': total_topics,
        'total_posts': total_posts,
        'active_subscriptions': active_subscriptions,
        'new_users_week': new_users_week,
        'total_badges': total_badges,
        'recent_users': recent_users,
        'pending_educator_profiles': pending_educator_profiles,
        'recent_topics': recent_topics,
        'users_by_month': json.dumps(users_by_month),
    }
    
    return render(request, 'authen/admin/dashboard.html', context)


# ========== GESTION DES UTILISATEURS ==========
@admin_required
def admin_users_list(request):
    """Liste de tous les utilisateurs"""
    
    # Filtres
    user_type = request.GET.get('type', 'all')
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    
    # Query de base
    users = User.objects.select_related('profile').all()
    
    # Appliquer les filtres
    if user_type != 'all':
        users = users.filter(profile__user_type=user_type)
    
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search)
        )
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'user_type': user_type,
        'status': status,
        'search': search,
    }
    
    return render(request, 'authen/admin/users_list.html', context)


@admin_required
def admin_user_detail(request, user_id):
    """Détails d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    # Enfants si parent
    enfants = Enfant.objects.filter(parent=user) if profile and profile.user_type == 'parent' else []
    
    # Activité forum
    topics = Topic.objects.filter(created_by=user).order_by('-created_at')[:5]
    posts = Post.objects.filter(created_by=user).order_by('-created_at')[:5]
    
    # Badges
    user_badges = UserBadge.objects.filter(user=user).select_related('badge')
    
    context = {
        'viewed_user': user,
        'profile': profile,
        'enfants': enfants,
        'topics': topics,
        'posts': posts,
        'user_badges': user_badges,
    }
    
    return render(request, 'authen/admin/user_detail.html', context)


@admin_required
def admin_approve_educator(request, user_id):
    """Approuver un éducateur + ENVOI EMAIL"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    user = get_object_or_404(User, id=user_id)
    
    # Activer le compte
    user.is_active = True
    user.save()
    
    # Créer une notification
    Notification.objects.create(
        user=user,
        notification_type='badge',
        message=f"✅ Votre compte éducateur a été approuvé ! Bienvenue sur ComAutiste.",
        link='/dashboard/'
    )
    
    # 📧 ENVOI D'EMAIL
    try:
        subject = "✅ Votre compte ComAutiste a été approuvé !"
        message = f"""
Bonjour {user.first_name or user.username},

Bonne nouvelle ! 🎉

Votre compte éducateur sur ComAutiste a été approuvé par notre équipe.

Vous pouvez maintenant vous connecter à votre espace :
👉 http://localhost:8000/login/

Vos identifiants :
📧 Nom d'utilisateur : {user.username}
🔐 Mot de passe : celui que vous avez choisi lors de l'inscription

Une fois connecté, vous pourrez :
✅ Suivre les enfants qui vous sont assignés
✅ Consulter leurs activités et progrès
✅ Ajouter des observations
✅ Accéder aux ressources pédagogiques

Si vous avez des questions, n'hésitez pas à nous contacter.

Bienvenue dans l'équipe ComAutiste ! 🌟

---
L'équipe ComAutiste
support@comautiste.fr
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        messages.success(request, f"✅ L'éducateur {user.username} a été approuvé et l'email a été envoyé !")
        
    except Exception as e:
        messages.warning(request, f"⚠️ {user.username} approuvé mais erreur d'envoi d'email : {str(e)}")
    
    return redirect('admin_dashboard')

@admin_required
def admin_deactivate_user(request, user_id):
    """Désactiver un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    user.is_active = False
    user.save()
    messages.warning(request, f"⚠️ L'utilisateur {user.username} a été désactivé.")
    return redirect('admin_users_list')


@admin_required
def admin_delete_user(request, user_id):
    """Supprimer un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    username = user.username
    user.delete()
    messages.error(request, f"🗑️ L'utilisateur {username} a été supprimé définitivement.")
    return redirect('admin_users_list')


# ========== GESTION DES ENFANTS ==========
@admin_required
def admin_enfants_list(request):
    """Liste de tous les enfants"""
    
    search = request.GET.get('search', '')
    
    enfants = Enfant.objects.select_related('parent').all()
    
    if search:
        enfants = enfants.filter(
            Q(prenom__icontains=search) |
            Q(nom__icontains=search) |
            Q(parent__username__icontains=search)
        )
    
    enfants = enfants.order_by('-created_at')
    
    context = {
        'enfants': enfants,
        'search': search,
    }
    
    return render(request, 'authen/admin/enfants_list.html', context)


# ========== MODÉRATION FORUM ==========
@admin_required
def admin_forum_moderation(request):
    """Modération du forum"""
    
    topics = Topic.objects.select_related('created_by').order_by('-created_at')
    posts = Post.objects.select_related('created_by', 'topic').order_by('-created_at')[:20]
    
    context = {
        'topics': topics,
        'posts': posts,
    }
    
    return render(request, 'authen/admin/forum_moderation.html', context)


@admin_required
def admin_delete_topic(request, topic_id):
    """Supprimer un topic"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    topic_title = topic.title
    topic.delete()
    messages.success(request, f"🗑️ Le topic '{topic_title}' a été supprimé.")
    return redirect('admin_forum_moderation')


@admin_required
def admin_delete_post(request, post_id):
    """Supprimer un post"""
    post = get_object_or_404(Post, id=post_id)
    
    post.delete()
    messages.success(request, f"🗑️ Le commentaire a été supprimé.")
    return redirect('admin_forum_moderation')


# ========== GESTION DES ABONNEMENTS ==========
@admin_required
def admin_subscriptions(request):
    """Gestion des abonnements"""
    
    try:
        subscriptions = Subscription.objects.select_related('parent').order_by('-start_date')
        
        active_subs = subscriptions.filter(active=True).count()
        expired_subs = subscriptions.filter(active=False).count()
    except Exception as e:
        # Si erreur, retourner des valeurs vides
        subscriptions = []
        active_subs = 0
        expired_subs = 0
    
    context = {
        'subscriptions': subscriptions,
        'active_subs': active_subs,
        'expired_subs': expired_subs,
    }
    
    return render(request, 'authen/admin/subscriptions.html', context)


# ========== STATISTIQUES AVANCÉES ==========
@admin_required
def admin_statistics(request):
    """Page de statistiques détaillées"""
    
    # Stats par genre d'enfant
    enfants_by_genre = Enfant.objects.values('genre').annotate(count=Count('id'))
    
    # Stats par niveau d'autonomie
    enfants_by_autonomie = Enfant.objects.values('niveau_autonomie').annotate(count=Count('id'))
    
    # Stats forum par catégorie
    topics_by_category = Topic.objects.values('category').annotate(count=Count('id'))
    
    context = {
        'enfants_by_genre': list(enfants_by_genre),
        'enfants_by_autonomie': list(enfants_by_autonomie),
        'topics_by_category': list(topics_by_category),
    }
    
    return render(request, 'authen/admin/statistics.html', context)