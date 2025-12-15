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
    Récupère les statistiques complètes d'un enfant avec calculs sécurisés
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
    
    # ✅ Calcul sécurisé du temps passé
    def calcul_temps_securise(queryset):
        """Calcule le temps total en minutes de façon sécurisée"""
        temps_total = 0
        for act in queryset:
            if act.duree_minutes and act.duree_minutes > 0:
                temps_total += act.duree_minutes
            elif act.date_fin and act.date_debut and act.date_fin > act.date_debut:
                duree = (act.date_fin - act.date_debut).total_seconds() / 60
                if 0 < duree < 1440:  # Entre 0 et 24h
                    temps_total += duree
        return int(temps_total)
    
    # Stats globales
    stats = {
        # Nombres d'activités
        'total_activites': total_count,
        'activites_today': activites_today.count(),
        'activites_week': activites_week.count(),
        'activites_month': activites_month.count(),
        
        # Temps passé (en minutes)
        'temps_total_minutes': calcul_temps_securise(activites),
        'temps_semaine_minutes': calcul_temps_securise(activites_week),
        'temps_aujourd_hui_minutes': calcul_temps_securise(activites_today),
        'temps_mois_minutes': calcul_temps_securise(activites_month),
        
        # Temps moyen par session
        'temps_moyen_minutes': int(calcul_temps_securise(activites) / max(total_count, 1)),
        
        # Jeux favoris (top 3) avec noms lisibles
        'jeux_favoris': [
            {
                'jeu': dict(Activite.JEUX_CHOICES).get(j['jeu'], j['jeu']),
                'count': j['count']
            }
            for j in activites.values('jeu').annotate(
                count=Count('jeu')
            ).order_by('-count')[:3]
        ],
        
        # Taux de réussite
        'taux_reussite': round((activites.filter(reussi=True).count() * 100 / max(total_count, 1)), 1),
        
        # Score moyen (si applicable)
        'score_moyen': int(activites.filter(score__isnull=False).aggregate(Avg('score'))['score__avg'] or 0),
        
        # Activité récente (dernier jeu joué)
        'derniere_activite': activites.order_by('-date_debut').first(),
        
        # Streak (jours consécutifs)
        'streak_jours': calculer_streak(enfant),
    }
    
    return stats

def get_activites_par_jour(enfant, jours=7):
    """
    Retourne le nombre d'activités par jour sur les X derniers jours
    Format : [{'jour': '15/12', 'date': date_obj, 'count': 5}, ...]
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
    
    # ✅ Créer un dictionnaire avec tous les jours (même ceux sans activité)
    result = []
    date_actuelle = debut.date()
    activites_dict = {item['jour']: item['count'] for item in activites_par_jour}
    
    for i in range(jours):
        jour_date = date_actuelle + timedelta(days=i)
        result.append({
            'jour': jour_date.strftime('%d/%m'),
            'date': jour_date,
            'count': activites_dict.get(jour_date, 0)  # 0 si aucune activité ce jour
        })
    
    return result

def get_temps_par_jeu(enfant, limit=5):
    """
    Retourne le temps passé par jeu (top X jeux) de façon sécurisée
    """
    activites = Activite.objects.filter(enfant=enfant)
    
    temps_par_jeu = {}
    for act in activites:
        jeu = act.jeu
        if jeu not in temps_par_jeu:
            temps_par_jeu[jeu] = {'temps_total': 0, 'nb_sessions': 0}
        
        # Calcul sécurisé du temps
        if act.duree_minutes and act.duree_minutes > 0:
            temps_par_jeu[jeu]['temps_total'] += act.duree_minutes
        elif act.date_fin and act.date_debut and act.date_fin > act.date_debut:
            duree = (act.date_fin - act.date_debut).total_seconds() / 60
            if 0 < duree < 1440:
                temps_par_jeu[jeu]['temps_total'] += int(duree)
        
        temps_par_jeu[jeu]['nb_sessions'] += 1
    
    # Trier et limiter
    result = [
        {'jeu': jeu, 'temps_total': data['temps_total'], 'nb_sessions': data['nb_sessions']}
        for jeu, data in sorted(temps_par_jeu.items(), key=lambda x: x[1]['temps_total'], reverse=True)[:limit]
    ]
    
    return result

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