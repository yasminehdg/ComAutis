from authen.models import Badge, UserBadge, Notification
from forum.models import Topic, Post, Reaction
from django.db.models import Count
from datetime import datetime, timedelta

def check_and_award_badges(user):
    """Vérifie et attribue les badges automatiquement"""
    badges_awarded = []
    
    # 1. Badge "Nouveau Parent" - Dès l'inscription
    badge_nouveau = Badge.objects.get(name='nouveau_parent')
    if not UserBadge.objects.filter(user=user, badge=badge_nouveau).exists():
        UserBadge.objects.create(user=user, badge=badge_nouveau)
        create_notification(user, 'badge', f"🎉 Vous avez obtenu le badge {badge_nouveau.icon} {badge_nouveau.get_name_display()} !")
        badges_awarded.append(badge_nouveau)
    
    # 2. Badge "Premier Pas" - Premier topic créé
    topic_count = Topic.objects.filter(created_by=user).count()
    if topic_count >= 1:
        badge_premier = Badge.objects.get(name='premier_pas')
        if not UserBadge.objects.filter(user=user, badge=badge_premier).exists():
            UserBadge.objects.create(user=user, badge=badge_premier)
            create_notification(user, 'badge', f"🎉 Vous avez obtenu le badge {badge_premier.icon} {badge_premier.get_name_display()} !")
            badges_awarded.append(badge_premier)
    
    # 3. Badge "Parent Engagé" - 10 topics/posts
    post_count = Post.objects.filter(created_by=user).count()
    total_posts = topic_count + post_count
    if total_posts >= 10:
        badge_engage = Badge.objects.get(name='parent_engage')
        if not UserBadge.objects.filter(user=user, badge=badge_engage).exists():
            UserBadge.objects.create(user=user, badge=badge_engage)
            create_notification(user, 'badge', f"🎉 Vous avez obtenu le badge {badge_engage.icon} {badge_engage.get_name_display()} !")
            badges_awarded.append(badge_engage)
    
    # 4. Badge "Parent Aidant" - 20 réactions reçues
    reactions_received = Reaction.objects.filter(topic__created_by=user).count()
    if reactions_received >= 20:
        badge_aidant = Badge.objects.get(name='parent_aidant')
        if not UserBadge.objects.filter(user=user, badge=badge_aidant).exists():
            UserBadge.objects.create(user=user, badge=badge_aidant)
            create_notification(user, 'badge', f"🎉 Vous avez obtenu le badge {badge_aidant.icon} {badge_aidant.get_name_display()} !")
            badges_awarded.append(badge_aidant)
    
    # 5. Badge "Pilier" - 50 messages
    if total_posts >= 50:
        badge_pilier = Badge.objects.get(name='pilier')
        if not UserBadge.objects.filter(user=user, badge=badge_pilier).exists():
            UserBadge.objects.create(user=user, badge=badge_pilier)
            create_notification(user, 'badge', f"🎉 Vous avez obtenu le badge {badge_pilier.icon} {badge_pilier.get_name_display()} !")
            badges_awarded.append(badge_pilier)
    
    # 6. Badge "Famille" - Membre depuis 6 mois
    six_months_ago = datetime.now() - timedelta(days=180)
    if user.date_joined <= six_months_ago.replace(tzinfo=user.date_joined.tzinfo):
        badge_famille = Badge.objects.get(name='famille')
        if not UserBadge.objects.filter(user=user, badge=badge_famille).exists():
            UserBadge.objects.create(user=user, badge=badge_famille)
            create_notification(user, 'badge', f"🎉 Vous avez obtenu le badge {badge_famille.icon} {badge_famille.get_name_display()} !")
            badges_awarded.append(badge_famille)
    
    return badges_awarded


def create_notification(user, notification_type, message, link=''):
    """Crée une notification pour l'utilisateur"""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message,
        link=link
    )