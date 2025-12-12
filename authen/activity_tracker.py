from .models import Activite
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate

def start_activity(enfant, jeu_name):
    """
    Démarre une nouvelle activité pour un enfant
    Retourne l'ID de l'activité créée
    """
    activite = Activite.objects.create(
        enfant=enfant,
        jeu=jeu_name,
        date_debut=timezone.now()
    )
    return activite.id

def end_activity(activite_id, score=None, reussi=True):
    """
    Termine une activité et calcule la durée
    """
    try:
        activite = Activite.objects.get(id=activite_id)
        activite.date_fin = timezone.now()
        activite.score = score
        activite.reussi = reussi
        activite.calculer_duree()
        return True
    except Activite.DoesNotExist:
        return False

def get_enfant_stats(enfant):
    """
    Récupère les statistiques complètes d'un enfant
    """
    # Toutes les activités de l'enfant
    activites = Activite.objects.filter(enfant=enfant)
    
    # Aujourd'hui
    today = timezone.now().date()
    activites_today = activites.filter(date_debut__date=today)
    
    # Cette semaine (7 derniers jours)
    week_ago = timezone.now() - timedelta(days=7)
    activites_week = activites.filter(date_debut__gte=week_ago)
    
    # Ce mois
    month_ago = timezone.now() - timedelta(days=30)
    activites_month = activites.filter(date_debut__gte=month_ago)
    
    # Calculer le total d'activités
    total_count = activites.count()
    
    # Stats globales
    stats = {
        # Nombres d'activités
        'total_activites': total_count,
        'activites_today': activites_today.count(),
        'activites_week': activites_week.count(),
        'activites_month': activites_month.count(),
        
        # Temps passé
        'temps_total_minutes': activites.aggregate(Sum('duree_minutes'))['duree_minutes__sum'] or 0,
        'temps_semaine_minutes': activites_week.aggregate(Sum('duree_minutes'))['duree_minutes__sum'] or 0,
        'temps_aujourd_hui_minutes': activites_today.aggregate(Sum('duree_minutes'))['duree_minutes__sum'] or 0,
        'temps_mois_minutes': activites_month.aggregate(Sum('duree_minutes'))['duree_minutes__sum'] or 0,
        
        # Temps moyen par session
        'temps_moyen_minutes': activites.aggregate(Avg('duree_minutes'))['duree_minutes__avg'] or 0,
        
        # Jeux favoris (top 3)
        'jeux_favoris': list(activites.values('jeu').annotate(
            count=Count('jeu'),
            nom_jeu=Count('jeu')
        ).order_by('-count')[:3]),
        
        # Taux de réussite
        'taux_reussite': round((activites.filter(reussi=True).count() * 100 / max(total_count, 1)), 1),
        
        # Score moyen (si applicable)
        'score_moyen': activites.filter(score__isnull=False).aggregate(Avg('score'))['score__avg'] or 0,
        
        # Activité récente (dernier jeu joué)
        'derniere_activite': activites.order_by('-date_debut').first(),
        
        # Streak (jours consécutifs)
        'streak_jours': calculer_streak(enfant),
    }
    
    return stats

def get_activites_par_jour(enfant, jours=7):
    """
    Retourne le nombre d'activités par jour sur les X derniers jours
    Format : [{'jour': '2025-01-10', 'count': 5}, ...]
    """
    debut = timezone.now() - timedelta(days=jours)
    
    activites_par_jour = Activite.objects.filter(
        enfant=enfant,
        date_debut__gte=debut
    ).annotate(
        jour=TruncDate('date_debut')
    ).values('jour').annotate(
        count=Count('id')
    ).order_by('jour')
    
    # Convertir en liste avec dates formatées
    result = []
    for item in activites_par_jour:
        result.append({
            'jour': item['jour'].strftime('%d/%m'),
            'date': item['jour'],
            'count': item['count']
        })
    
    return result

def get_temps_par_jeu(enfant, limit=5):
    """
    Retourne le temps passé par jeu (top X jeux)
    """
    temps_par_jeu = Activite.objects.filter(enfant=enfant).values('jeu').annotate(
        temps_total=Sum('duree_minutes'),
        nb_sessions=Count('id')
    ).order_by('-temps_total')[:limit]
    
    return list(temps_par_jeu)

def calculer_streak(enfant):
    """
    Calcule le nombre de jours consécutifs où l'enfant a joué
    """
    activites = Activite.objects.filter(enfant=enfant).order_by('-date_debut')
    
    if not activites.exists():
        return 0
    
    streak = 0
    date_actuelle = timezone.now().date()
    
    # Vérifier si joué aujourd'hui
    if activites.filter(date_debut__date=date_actuelle).exists():
        streak = 1
    else:
        # Vérifier si joué hier
        hier = date_actuelle - timedelta(days=1)
        if not activites.filter(date_debut__date=hier).exists():
            return 0
        date_actuelle = hier
        streak = 1
    
    # Compter les jours consécutifs
    for i in range(1, 365):  # Maximum 1 an
        jour_precedent = date_actuelle - timedelta(days=i)
        if activites.filter(date_debut__date=jour_precedent).exists():
            streak += 1
        else:
            break
    
    return streak

def get_progression_mensuelle(enfant):
    """
    Retourne la progression sur les 30 derniers jours
    """
    debut = timezone.now() - timedelta(days=30)
    
    activites = Activite.objects.filter(
        enfant=enfant,
        date_debut__gte=debut
    ).annotate(
        jour=TruncDate('date_debut')
    ).values('jour').annotate(
        count=Count('id'),
        temps_total=Sum('duree_minutes')
    ).order_by('jour')
    
    return list(activites)

def get_jeux_recents(enfant, limit=5):
    """
    Retourne les X derniers jeux joués
    """
    return Activite.objects.filter(enfant=enfant).order_by('-date_debut')[:limit]

def creer_activite_test(enfant, jeu_name, duree_minutes=10, score=None, reussi=True, date_personnalisee=None):
    """
    Crée une activité de test avec une date personnalisée
    Utile pour générer des données de démonstration
    """
    date = date_personnalisee if date_personnalisee else timezone.now()
    date_fin = date + timedelta(minutes=duree_minutes)
    
    activite = Activite.objects.create(
        enfant=enfant,
        jeu=jeu_name,
        date_debut=date,
        date_fin=date_fin,
        duree_minutes=duree_minutes,
        score=score,
        reussi=reussi
    )
    
    return activite