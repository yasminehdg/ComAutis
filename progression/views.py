from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from .models import (
    Contenu, Categorie, EnfantProgression,
    HistoriqueActivite, Badge, BadgeObtenu,
    EvaluationContenu, NiveauContenu
)
from .forms import (
    ContenuForm, CategorieForm, ContenuFiltreForm,
    BadgeForm, EvaluationContenuForm, NiveauContenuForm,
    ExportRapportForm
)


# ============================================
# DASHBOARD ADMIN
# ============================================

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def dashboard_admin(request):
    """
    Dashboard principal pour les administrateurs
    Affiche les statistiques et la liste des éducateurs
    """
    from authen.models import ProfilEducateur
    
    # Statistiques générales
    stats = {
        'total_educateurs': ProfilEducateur.objects.filter(est_actif=True).count(),
        'total_enfants': EnfantProgression.objects.count(),
        'total_contenus': Contenu.objects.count(),
        'educateurs_en_attente': ProfilEducateur.objects.filter(
            est_actif=True,
            est_valide=False
        ).count(),
    }
    
    # Éducateurs en attente de validation
    educateurs_en_attente = ProfilEducateur.objects.filter(
        est_actif=True,
        est_valide=False
    ).select_related('user').order_by('-user__date_joined')
    
    # Éducateurs actifs
    educateurs_actifs = ProfilEducateur.objects.filter(
        est_actif=True,
        est_valide=True
    ).select_related('user').prefetch_related('enfants_suivis').order_by('user__username')
    
    context = {
        'stats': stats,
        'educateurs_en_attente': educateurs_en_attente,
        'educateurs_actifs': educateurs_actifs,
    }
    
    return render(request, 'progression/dashboard_admin.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_valider_educateur(request, educateur_id):
    """
    Valider un éducateur en attente
    """
    from authen.models import ProfilEducateur
    
    educateur = get_object_or_404(ProfilEducateur, id=educateur_id)
    
    if not educateur.est_valide:
        educateur.est_valide = True
        educateur.save()
        
        messages.success(
            request,
            f"✅ L'éducateur {educateur.user.get_full_name() or educateur.user.username} a été validé avec succès !"
        )
    else:
        messages.info(request, "ℹ️ Cet éducateur est déjà validé.")
    
    return redirect('dashboard_admin')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_desactiver_educateur(request, educateur_id):
    """
    Désactiver un éducateur
    """
    from authen.models import ProfilEducateur
    
    educateur = get_object_or_404(ProfilEducateur, id=educateur_id)
    
    if educateur.est_actif:
        educateur.est_actif = False
        educateur.save()
        
        messages.warning(
            request,
            f"⚠️ L'éducateur {educateur.user.get_full_name() or educateur.user.username} a été désactivé."
        )
    else:
        messages.info(request, "ℹ️ Cet éducateur est déjà désactivé.")
    
    return redirect('dashboard_admin')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_statistiques_globales(request):
    """
    Page de statistiques globales du système
    """
    from authen.models import ProfilEducateur, ProfilFamille
    from django.db.models import Count, Avg, Sum
    from datetime import datetime, timedelta
    
    # Période (derniers 30 jours)
    date_debut = datetime.now() - timedelta(days=30)
    
    # Statistiques utilisateurs
    stats_utilisateurs = {
        'total_educateurs': ProfilEducateur.objects.filter(est_actif=True).count(),
        'educateurs_valides': ProfilEducateur.objects.filter(
            est_actif=True, 
            est_valide=True
        ).count(),
        'total_familles': ProfilFamille.objects.count(),
        'total_enfants': EnfantProgression.objects.count(),
    }
    
    # Statistiques contenus
    stats_contenus = {
        'total_contenus': Contenu.objects.count(),
        'contenus_actifs': Contenu.objects.filter(est_actif=True).count(),
        'contenus_valides': Contenu.objects.filter(est_valide=True).count(),
        'contenus_par_type': Contenu.objects.values('type_contenu').annotate(
            count=Count('id')
        ).order_by('-count'),
        'contenus_recents': Contenu.objects.filter(
            date_creation__gte=date_debut
        ).count(),
    }
    
    # Statistiques activités
    stats_activites = {
        'total_activites': HistoriqueActivite.objects.count(),
        'activites_30j': HistoriqueActivite.objects.filter(
            date_activite__gte=date_debut
        ).count(),
        'activites_par_type': HistoriqueActivite.objects.values(
            'type_activite'
        ).annotate(count=Count('id')).order_by('-count'),
    }
    
    # Statistiques badges
    stats_badges = {
        'total_badges': Badge.objects.count(),
        'badges_obtenus': BadgeObtenu.objects.count(),
        'badges_30j': BadgeObtenu.objects.filter(
            date_obtention__gte=date_debut
        ).count(),
    }
    
    # Progression moyenne
    progression_moyenne = EnfantProgression.objects.aggregate(
        niveau_moyen=Avg('niveau_actuel'),
        score_moyen=Avg('score_total'),
    )
    
    context = {
        'stats_utilisateurs': stats_utilisateurs,
        'stats_contenus': stats_contenus,
        'stats_activites': stats_activites,
        'stats_badges': stats_badges,
        'progression_moyenne': progression_moyenne,
        'date_debut': date_debut,
    }
    
    return render(request, 'progression/admin_statistiques.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_gestion_educateurs(request):
    """
    Page de gestion complète des éducateurs
    """
    from authen.models import ProfilEducateur
    from django.db.models import Count
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Query de base
    educateurs = ProfilEducateur.objects.select_related('user').prefetch_related('enfants_suivis')
    
    # Appliquer les filtres
    if status_filter == 'active':
        educateurs = educateurs.filter(est_actif=True, est_valide=True)
    elif status_filter == 'pending':
        educateurs = educateurs.filter(est_actif=True, est_valide=False)
    elif status_filter == 'inactive':
        educateurs = educateurs.filter(est_actif=False)
    
    if search_query:
        educateurs = educateurs.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(specialite__icontains=search_query)
        )
    
    # Annoter avec le nombre d'enfants
    educateurs = educateurs.annotate(
        nb_enfants=Count('enfants_suivis')
    ).order_by('-user__date_joined')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(educateurs, 20)  # 20 par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'educateurs': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': educateurs.count(),
    }
    
    return render(request, 'progression/admin_gestion_educateurs.html', context)



def dashboard_progression(request):
    """
    Point d'entrée principal : redirige selon le type d'utilisateur
    """
    user = request.user
    
    # Si l'utilisateur n'est pas connecté
    if not user.is_authenticated:
        return redirect('login')  # Remplace 'login' par le nom de ta page de connexion
    
    # Si c'est un enfant (via session parent)
    if request.session.get('enfant_id'):
        enfant_id = request.session.get('enfant_id')
        return redirect('progression_enfant_detail', enfant_id=enfant_id)
    
    # Si c'est un parent (vérifie selon ta structure)
    # Tu dois adapter selon comment tu gères les rôles dans ton projet
    # Exemple : if hasattr(user, 'parent'):
    #     return redirect('dashboard_parent')
    
    # Si c'est un éducateur
    # Exemple : elif hasattr(user, 'educateur'):
    #     return redirect('dashboard_educateur')
    
    # Par défaut : afficher la liste des enfants
    return redirect('liste_enfants')


def dashboard_parent(request):
    """
    Dashboard pour les parents : voir tous leurs enfants
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # ⚠️ À ADAPTER selon ta structure de données
    # Exemple simple : on prend toutes les progressions pour tester
    progressions_data = []
    progressions = EnfantProgression.objects.all()
    
    for prog in progressions:
        progressions_data.append({
            'progression': prog,
            'pourcentage': prog.pourcentage_progression()
        })
    
    context = {
        'progressions': progressions_data
    }
    
    return render(request, 'progression/dashboard_parent.html', context)


def dashboard_educateur(request):
    """
    Dashboard pour les éducateurs : statistiques globales
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Récupérer le profil éducateur
    try:
        from authen.models import ProfilEducateur
        profil_educateur = ProfilEducateur.objects.get(user=request.user, est_actif=True)
        
        # ✅ Récupérer UNIQUEMENT les enfants suivis par cet éducateur
        progressions = profil_educateur.enfants_suivis.all()
    except ProfilEducateur.DoesNotExist:
        # Si pas de profil éducateur, afficher tous les enfants (fallback)
        progressions = EnfantProgression.objects.all()
    
    from django.db.models import Avg, Sum
    from django.utils import timezone
    from datetime import timedelta
    
    # Calculer les statistiques
    total_enfants = progressions.count()
    niveau_moyen = progressions.aggregate(Avg('niveau'))['niveau__avg'] or 0
    score_total = progressions.aggregate(Sum('score'))['score__sum'] or 0
    
    # Activités de la semaine
    semaine_derniere = timezone.now() - timedelta(days=7)
    activites_semaine = progressions.filter(
        date_modification__gte=semaine_derniere
    ).aggregate(Sum('activites_terminees'))['activites_terminees__sum'] or 0
    
    # Liste des enfants avec leurs infos
    enfants_data = []
    for prog in progressions:
        # Calculer le temps depuis la dernière activité
        temps_ecoule = timezone.now() - prog.date_modification
        if temps_ecoule.days > 0:
            derniere_activite = f"Il y a {temps_ecoule.days} jour{'s' if temps_ecoule.days > 1 else ''}"
        elif temps_ecoule.seconds // 3600 > 0:
            heures = temps_ecoule.seconds // 3600
            derniere_activite = f"Il y a {heures}h"
        else:
            minutes = temps_ecoule.seconds // 60
            derniere_activite = f"Il y a {minutes}min"
        
        enfants_data.append({
            'progression': prog,
            'pourcentage': prog.pourcentage_progression(),
            'derniere_activite': derniere_activite
        })
    
    # Trier par niveau décroissant
    enfants_data.sort(key=lambda x: x['progression'].niveau, reverse=True)
    
    stats = {
        'total_enfants': total_enfants,
        'niveau_moyen': round(niveau_moyen, 1),
        'score_total': score_total,
        'activites_semaine': activites_semaine,
    }
    
    context = {
        'stats': stats,
        'enfants': enfants_data,
    }
    
    return render(request, 'progression/dashboard_educateur.html', context)


def detail_enfant_educateur(request, enfant_id):
    """
    Vue détaillée d'un enfant pour l'éducateur
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    progression = get_object_or_404(EnfantProgression, id=enfant_id)
    
    # Calculer des statistiques supplémentaires
    from django.utils import timezone
    from datetime import timedelta
    
    # Progression cette semaine
    semaine_derniere = timezone.now() - timedelta(days=7)
    score_debut_semaine = progression.score  # Simplification
    progression_semaine = 0  # À améliorer avec un historique
    
    context = {
        'progression': progression,
        'pourcentage': progression.pourcentage_progression(),
        'message': progression.message_motivation(),
        'points_necessaires': progression.points_pour_niveau_suivant(),
        'score_actuel': progression.score_pour_niveau_actuel(),
        'progression_semaine': progression_semaine,
    }
    
    return render(request, 'progression/detail_enfant_educateur.html', context)

def progression_enfant(request, enfant_id=None):
    """
    Vue principale pour afficher la progression d'un enfant
    Si enfant_id n'est pas fourni, on prend le premier enfant (pour les tests)
    """
    if enfant_id:
        progression = get_object_or_404(EnfantProgression, id=enfant_id)
    else:
        # Pour les tests, prendre le premier enfant ou en créer un
        progression = EnfantProgression.objects.first()
        if not progression:
            # Créer un enfant de test
            progression = EnfantProgression.objects.create(
                nom_enfant="Alex",
                niveau=1,
                score=0,
                activites_terminees=0,
                activites_totales=10
            )
    
    context = {
        'progression': progression,
        'pourcentage': progression.pourcentage_progression(),
        'message': progression.message_motivation(),
        'points_necessaires': progression.points_pour_niveau_suivant(),
        'score_actuel': progression.score_pour_niveau_actuel(),
    }
    
    return render(request, 'progression/progression_enfant.html', context)


def liste_enfants(request):
    """
    Vue pour lister tous les enfants et leur progression
    """
    progressions = EnfantProgression.objects.all().order_by('-niveau', '-score')
    
    context = {
        'progressions': progressions,
    }
    
    return render(request, 'progression/liste_enfants.html', context)


def terminer_activite(request, enfant_id):
    """
    Vue pour marquer une activité comme terminée
    Ajoute des points et vérifie le passage de niveau
    """
    if request.method == 'POST':
        progression = get_object_or_404(EnfantProgression, id=enfant_id)
        
        # Récupérer le nombre de points (par défaut 20)
        points = int(request.POST.get('points', 20))
        
        # Terminer l'activité
        progression.terminer_activite(points)
        
        # Retourner une réponse JSON pour une mise à jour dynamique
        return JsonResponse({
            'success': True,
            'nouveau_score': progression.score,
            'nouveau_niveau': progression.niveau,
            'activites_terminees': progression.activites_terminees,
            'pourcentage': progression.pourcentage_progression(),
            'message': progression.message_motivation(),
            'niveau_monte': progression.niveau > progression.niveau - 1
        })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def reinitialiser_progression(request, enfant_id):
    """
    Vue pour réinitialiser la progression d'un enfant (pour les tests)
    """
    if request.method == 'POST':
        progression = get_object_or_404(EnfantProgression, id=enfant_id)
        progression.niveau = 1
        progression.score = 0
        progression.activites_terminees = 0
        progression.activites_totales = 10
        progression.save()
        
        return redirect('progression_enfant_detail', enfant_id=enfant_id)
    
    return redirect('progression_enfant_detail', enfant_id=enfant_id)


def simuler_activite(request, enfant_id):
    """
    Vue de test pour simuler la complétion d'une activité
    """
    progression = get_object_or_404(EnfantProgression, id=enfant_id)
    progression.terminer_activite(points=20)
    
    return redirect('progression_enfant_detail', enfant_id=enfant_id)


def enregistrer_activite_reussie(enfant_id, type_activite, points=20):
    """
    Fonction utilitaire pour enregistrer une activité réussie
    À appeler depuis les autres apps (jeux, videos, coloriages, etc.)
    
    Args:
        enfant_id: ID de l'enfant
        type_activite: Type d'activité ('jeu', 'video', 'coloriage', etc.)
        points: Nombre de points à attribuer (par défaut 20)
    
    Returns:
        dict: Informations sur la progression mise à jour
    """
    try:
        progression = EnfantProgression.objects.get(id=enfant_id)
        ancien_niveau = progression.niveau
        
        # Enregistrer l'activité
        progression.terminer_activite(points=points)
        
        # Vérifier si le niveau a changé
        niveau_monte = progression.niveau > ancien_niveau
        
        return {
            'success': True,
            'nouveau_score': progression.score,
            'nouveau_niveau': progression.niveau,
            'niveau_monte': niveau_monte,
            'message': progression.message_motivation()
        }
    except EnfantProgression.DoesNotExist:
        return {
            'success': False,
            'error': 'Progression non trouvée'
        }
    
    # Gérer les enfants par Educateur
@login_required
def gerer_enfants_educateur(request):
    """
    Interface pour que l'éducateur gère les enfants qu'il suit
    """
    try:
        from authen.models import ProfilEducateur
        profil_educateur = ProfilEducateur.objects.get(user=request.user, est_actif=True)
    except ProfilEducateur.DoesNotExist:
        messages.error(request, "❌ Vous devez avoir un profil éducateur pour accéder à cette page")
        return redirect('dashboard')
    
    # Tous les enfants disponibles
    tous_enfants = EnfantProgression.objects.all()
    
    # Enfants déjà suivis par cet éducateur
    enfants_suivis = profil_educateur.enfants_suivis.all()
    enfants_suivis_ids = list(enfants_suivis.values_list('id', flat=True))
    
    # Enfants disponibles (pas encore suivis)
    enfants_disponibles = tous_enfants.exclude(id__in=enfants_suivis_ids)
    
    context = {
        'profil_educateur': profil_educateur,
        'enfants_suivis': enfants_suivis,
        'enfants_disponibles': enfants_disponibles,
    }
    
    return render(request, 'progression/gerer_enfants_educateur.html', context)


@login_required
def ajouter_enfant_educateur(request, enfant_id):
    """
    Ajouter un enfant à la liste de l'éducateur
    """
    try:
        from authen.models import ProfilEducateur
        profil_educateur = ProfilEducateur.objects.get(user=request.user, est_actif=True)
        enfant = get_object_or_404(EnfantProgression, id=enfant_id)
        
        # Ajouter l'enfant
        profil_educateur.enfants_suivis.add(enfant)
        profil_educateur.save()
        
        messages.success(request, f"✅ {enfant.nom_enfant} a été ajouté à votre liste !")
    except ProfilEducateur.DoesNotExist:
        messages.error(request, "❌ Profil éducateur introuvable")
    
    return redirect('gerer_enfants_educateur')


@login_required
def retirer_enfant_educateur(request, enfant_id):
    """
    Retirer un enfant de la liste de l'éducateur
    """
    try:
        from authen.models import ProfilEducateur
        profil_educateur = ProfilEducateur.objects.get(user=request.user, est_actif=True)
        enfant = get_object_or_404(EnfantProgression, id=enfant_id)
        
        # Retirer l'enfant
        profil_educateur.enfants_suivis.remove(enfant)
        profil_educateur.save()
        
        messages.success(request, f"✅ {enfant.nom_enfant} a été retiré de votre liste")
    except ProfilEducateur.DoesNotExist:
        messages.error(request, "❌ Profil éducateur introuvable")
    
    return redirect('gerer_enfants_educateur')


# ============================================
# VÉRIFICATIONS DE PERMISSIONS
# ============================================

def est_educateur(user):
    """Vérifie si l'utilisateur est un éducateur"""
    if user.is_superuser:
        return True
    try:
        from authen.models import ProfilEducateur
        return ProfilEducateur.objects.filter(user=user, est_actif=True).exists()
    except:
        return False


def est_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_superuser or user.is_staff


# ============================================
# GESTION DES CONTENUS - LISTE ET FILTRES
# ============================================

@login_required
@user_passes_test(est_educateur, login_url='/')
def gestion_contenus(request):
    """
    Interface principale de gestion des contenus éducatifs
    Accessible aux éducateurs et administrateurs
    """
    contenus = Contenu.objects.select_related('categorie', 'cree_par').all()
    
    # Appliquer les filtres
    form_filtre = ContenuFiltreForm(request.GET)
    
    if form_filtre.is_valid():
        # Filtrer par type
        type_contenu = form_filtre.cleaned_data.get('type_contenu')
        if type_contenu:
            contenus = contenus.filter(type_contenu=type_contenu)
        
        # Filtrer par catégorie
        categorie = form_filtre.cleaned_data.get('categorie')
        if categorie:
            contenus = contenus.filter(categorie=categorie)
        
        # Filtrer par niveau
        niveau = form_filtre.cleaned_data.get('niveau')
        if niveau:
            contenus = contenus.filter(
                niveau_min__lte=niveau,
                niveau_max__gte=niveau
            )
        
        # Filtrer par difficulté
        difficulte = form_filtre.cleaned_data.get('difficulte')
        if difficulte:
            contenus = contenus.filter(difficulte=difficulte)
        
        # Filtrer par validation
        est_valide = form_filtre.cleaned_data.get('est_valide')
        if est_valide == '1':
            contenus = contenus.filter(est_valide=True)
        elif est_valide == '0':
            contenus = contenus.filter(est_valide=False)
        
        # Recherche textuelle
        recherche = form_filtre.cleaned_data.get('recherche')
        if recherche:
            contenus = contenus.filter(
                Q(titre__icontains=recherche) |
                Q(description__icontains=recherche) |
                Q(tags__icontains=recherche)
            )
    
    # Statistiques globales
    stats = {
        'total': contenus.count(),
        'actifs': contenus.filter(est_actif=True).count(),
        'valides': contenus.filter(est_valide=True).count(),
        'en_attente': contenus.filter(est_valide=False).count(),
    }
    
    # Pagination
    paginator = Paginator(contenus, 12)  # 12 contenus par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Catégories pour affichage rapide
    categories = Categorie.objects.filter(est_active=True).annotate(
        nb_contenus=Count('contenus')
    )
    
    context = {
        'page_obj': page_obj,
        'form_filtre': form_filtre,
        'stats': stats,
        'categories': categories,
    }
    
    return render(request, 'progression/gestion_contenus.html', context)


# ============================================
# CRUD CONTENUS
# ============================================

@login_required
@user_passes_test(est_educateur, login_url='/')
def creer_contenu(request):
    """Créer un nouveau contenu éducatif"""
    
    if request.method == 'POST':
        form = ContenuForm(request.POST, request.FILES)
        if form.is_valid():
            contenu = form.save(commit=False)
            contenu.cree_par = request.user
            
            # Si l'utilisateur est admin, valider automatiquement
            if est_admin(request.user):
                contenu.est_valide = True
            
            contenu.save()
            messages.success(request, f"✅ Le contenu '{contenu.titre}' a été créé avec succès !")
            return redirect('gestion_contenus')
        else:
            messages.error(request, "❌ Erreur lors de la création du contenu. Vérifiez les champs.")
    else:
        form = ContenuForm()
    
    context = {
        'form': form,
        'titre_page': 'Créer un nouveau contenu',
        'action': 'creer',
    }
    
    return render(request, 'progression/form_contenu.html', context)


@login_required
@user_passes_test(est_educateur, login_url='/')
def modifier_contenu(request, contenu_id):
    """Modifier un contenu existant"""
    
    contenu = get_object_or_404(Contenu, id=contenu_id)
    
    # Vérifier les permissions
    if not est_admin(request.user) and contenu.cree_par != request.user:
        messages.error(request, "❌ Vous n'avez pas la permission de modifier ce contenu.")
        return redirect('gestion_contenus')
    
    if request.method == 'POST':
        form = ContenuForm(request.POST, request.FILES, instance=contenu)
        if form.is_valid():
            contenu = form.save(commit=False)
            contenu.modifie_par = request.user
            contenu.save()
            messages.success(request, f"✅ Le contenu '{contenu.titre}' a été modifié avec succès !")
            return redirect('detail_contenu', contenu_id=contenu.id)
        else:
            messages.error(request, "❌ Erreur lors de la modification.")
    else:
        form = ContenuForm(instance=contenu)
    
    context = {
        'form': form,
        'contenu': contenu,
        'titre_page': 'Modifier le contenu',
        'action': 'modifier',
    }
    
    return render(request, 'progression/form_contenu.html', context)


@login_required
@user_passes_test(est_educateur, login_url='/')
def detail_contenu(request, contenu_id):
    """Afficher les détails d'un contenu"""
    
    contenu = get_object_or_404(Contenu, id=contenu_id)
    
    # Statistiques d'utilisation
    nb_enfants_niveau = EnfantProgression.objects.filter(
        niveau__gte=contenu.niveau_min,
        niveau__lte=contenu.niveau_max
    ).count()
    
    # Évaluations
    evaluations = contenu.evaluations.all()
    peut_evaluer = not evaluations.filter(utilisateur=request.user).exists()
    
    context = {
        'contenu': contenu,
        'nb_enfants_niveau': nb_enfants_niveau,
        'evaluations': evaluations,
        'peut_evaluer': peut_evaluer,
    }
    
    return render(request, 'progression/detail_contenu.html', context)


@login_required
@user_passes_test(est_admin, login_url='/')
def supprimer_contenu(request, contenu_id):
    """Supprimer un contenu (admin uniquement)"""
    
    contenu = get_object_or_404(Contenu, id=contenu_id)
    
    if request.method == 'POST':
        titre = contenu.titre
        contenu.delete()
        messages.success(request, f"✅ Le contenu '{titre}' a été supprimé.")
        return redirect('gestion_contenus')
    
    context = {
        'contenu': contenu,
    }
    
    return render(request, 'progression/supprimer_contenu_confirm.html', context)


@login_required
@user_passes_test(est_admin, login_url='/')
def valider_contenu(request, contenu_id):
    """Valider un contenu (admin uniquement)"""
    
    contenu = get_object_or_404(Contenu, id=contenu_id)
    contenu.est_valide = True
    contenu.save()
    
    messages.success(request, f"✅ Le contenu '{contenu.titre}' a été validé.")
    return redirect('detail_contenu', contenu_id=contenu.id)


@login_required
@user_passes_test(est_educateur, login_url='/')
def dupliquer_contenu(request, contenu_id):
    """Dupliquer un contenu existant"""
    
    contenu = get_object_or_404(Contenu, id=contenu_id)
    
    # Créer une copie
    nouveau_contenu = Contenu.objects.get(pk=contenu.pk)
    nouveau_contenu.pk = None
    nouveau_contenu.titre = f"{contenu.titre} (Copie)"
    nouveau_contenu.cree_par = request.user
    nouveau_contenu.est_valide = False
    nouveau_contenu.nombre_vues = 0
    nouveau_contenu.nombre_completions = 0
    nouveau_contenu.save()
    
    messages.success(request, f"✅ Le contenu a été dupliqué. Vous pouvez maintenant le modifier.")
    return redirect('modifier_contenu', contenu_id=nouveau_contenu.id)


# ============================================
# GESTION DES CATÉGORIES
# ============================================

@login_required
@user_passes_test(est_admin, login_url='/')
def gestion_categories(request):
    """Gérer les catégories de contenus"""
    
    categories = Categorie.objects.annotate(
        nb_contenus=Count('contenus')
    ).order_by('ordre_affichage', 'nom')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'progression/gestion_categories.html', context)


@login_required
@user_passes_test(est_admin, login_url='/')
def creer_categorie(request):
    """Créer une nouvelle catégorie"""
    
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            categorie = form.save()
            messages.success(request, f"✅ La catégorie '{categorie.nom}' a été créée !")
            return redirect('gestion_categories')
    else:
        form = CategorieForm()
    
    context = {
        'form': form,
        'action': 'creer',
    }
    
    return render(request, 'progression/form_categorie.html', context)


@login_required
@user_passes_test(est_admin, login_url='/')
def modifier_categorie(request, categorie_id):
    """Modifier une catégorie"""
    
    categorie = get_object_or_404(Categorie, id=categorie_id)
    
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ La catégorie '{categorie.nom}' a été modifiée !")
            return redirect('gestion_categories')
    else:
        form = CategorieForm(instance=categorie)
    
    context = {
        'form': form,
        'categorie': categorie,
        'action': 'modifier',
    }
    
    return render(request, 'progression/form_categorie.html', context)


# ============================================
# ASSIGNATION DE CONTENUS AUX NIVEAUX
# ============================================

@login_required
@user_passes_test(est_admin, login_url='/')
def gestion_niveaux_contenus(request):
    """Gérer l'assignation des contenus aux niveaux"""
    
    niveaux = range(1, 21)  # 20 niveaux
    
    # Récupérer les contenus assignés par niveau
    contenus_par_niveau = {}
    for niveau in niveaux:
        contenus_par_niveau[niveau] = NiveauContenu.objects.filter(
            niveau=niveau
        ).select_related('contenu').order_by('ordre_dans_niveau')
    
    context = {
        'niveaux': niveaux,
        'contenus_par_niveau': contenus_par_niveau,
    }
    
    return render(request, 'progression/gestion_niveaux_contenus.html', context)


@login_required
@user_passes_test(est_admin, login_url='/')
def assigner_contenu_niveau(request):
    """Assigner un contenu à un niveau"""
    
    if request.method == 'POST':
        form = NiveauContenuForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Contenu assigné au niveau avec succès !")
            return redirect('gestion_niveaux_contenus')
    else:
        form = NiveauContenuForm()
    
    contenus_disponibles = Contenu.objects.filter(est_actif=True, est_valide=True)
    
    context = {
        'form': form,
        'contenus_disponibles': contenus_disponibles,
    }
    
    return render(request, 'progression/form_niveau_contenu.html', context)


# ============================================
# ÉVALUATIONS DE CONTENUS
# ============================================

@login_required
def evaluer_contenu(request, contenu_id):
    """Évaluer un contenu"""
    
    contenu = get_object_or_404(Contenu, id=contenu_id)
    
    # Vérifier si l'utilisateur a déjà évalué
    evaluation_existante = EvaluationContenu.objects.filter(
        contenu=contenu,
        utilisateur=request.user
    ).first()
    
    if request.method == 'POST':
        if evaluation_existante:
            form = EvaluationContenuForm(request.POST, instance=evaluation_existante)
        else:
            form = EvaluationContenuForm(request.POST)
        
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.contenu = contenu
            evaluation.utilisateur = request.user
            evaluation.save()
            
            # Mettre à jour la note moyenne du contenu
            notes = contenu.evaluations.all()
            note_moyenne = notes.aggregate(Avg('note'))['note__avg']
            contenu.note_moyenne = note_moyenne or 0
            contenu.save(update_fields=['note_moyenne'])
            
            messages.success(request, "✅ Merci pour votre évaluation !")
            return redirect('detail_contenu', contenu_id=contenu.id)
    else:
        if evaluation_existante:
            form = EvaluationContenuForm(instance=evaluation_existante)
        else:
            form = EvaluationContenuForm()
    
    context = {
        'form': form,
        'contenu': contenu,
        'evaluation_existante': evaluation_existante,
    }
    
    return render(request, 'progression/evaluer_contenu.html', context)


# ============================================
# BIBLIOTHÈQUE DE CONTENUS (POUR ENFANTS)
# ============================================

@login_required
def bibliotheque_contenus(request, enfant_id=None):
    """
    Bibliothèque de contenus accessible pour un enfant
    Filtre automatiquement selon le niveau de l'enfant
    """
    
    # Récupérer la progression de l'enfant
    if enfant_id:
        progression = get_object_or_404(EnfantProgression, id=enfant_id)
    else:
        # Prendre le premier enfant (mode test)
        progression = EnfantProgression.objects.first()
    
    # Contenus accessibles selon le niveau
    contenus = Contenu.objects.filter(
        est_actif=True,
        est_valide=True,
        niveau_min__lte=progression.niveau,
        niveau_max__gte=progression.niveau
    ).select_related('categorie')
    
    # Filtrer par type si demandé
    type_filtre = request.GET.get('type')
    if type_filtre:
        contenus = contenus.filter(type_contenu=type_filtre)
    
    # Filtrer par catégorie si demandé
    categorie_id = request.GET.get('categorie')
    if categorie_id:
        contenus = contenus.filter(categorie_id=categorie_id)
    
    # Organiser par catégorie
    categories = Categorie.objects.filter(est_active=True)
    contenus_par_categorie = {}
    for categorie in categories:
        contenus_categorie = contenus.filter(categorie=categorie)
        if contenus_categorie.exists():
            contenus_par_categorie[categorie] = contenus_categorie
    
    context = {
        'progression': progression,
        'contenus_par_categorie': contenus_par_categorie,
        'categories': categories,
        'type_filtre': type_filtre,
    }
    
    return render(request, 'progression/bibliotheque_contenus.html', context)


@login_required
def jouer_contenu(request, contenu_id, enfant_id):
    """
    Lancer une activité de contenu et incrémenter les statistiques
    """
    
    contenu = get_object_or_404(Contenu, id=contenu_id)
    progression = get_object_or_404(EnfantProgression, id=enfant_id)
    
    # Vérifier que l'enfant a le niveau requis
    if not contenu.est_accessible_pour_niveau(progression.niveau):
        messages.error(request, "❌ Ce contenu n'est pas encore accessible pour ton niveau.")
        return redirect('bibliotheque_contenus', enfant_id=enfant_id)
    
    # Incrémenter les vues
    contenu.incrementer_vues()
    
    # Créer une entrée dans l'historique
    HistoriqueActivite.objects.create(
        enfant=progression,
        type_activite=contenu.type_contenu,
        nom_activite=contenu.titre,
        points_gagnes=0,  # Sera mis à jour à la fin
        reussite=False  # Sera mis à jour à la fin
    )
    
    context = {
        'contenu': contenu,
        'progression': progression,
    }
    
    # Rediriger vers le bon type de contenu
    if contenu.type_contenu == 'jeu':
        return render(request, 'progression/jouer_jeu.html', context)
    elif contenu.type_contenu == 'video':
        return render(request, 'progression/regarder_video.html', context)
    elif contenu.type_contenu == 'son':
        return render(request, 'progression/ecouter_son.html', context)
    elif contenu.type_contenu == 'coloriage':
        return render(request, 'progression/colorier.html', context)
    else:
        return render(request, 'progression/afficher_contenu.html', context)


# ============================================
# API AJAX
# ============================================

@login_required
def toggle_contenu_actif(request, contenu_id):
    """Toggle le statut actif d'un contenu"""
    
    if request.method == 'POST':
        contenu = get_object_or_404(Contenu, id=contenu_id)
        contenu.est_actif = not contenu.est_actif
        contenu.save()
        
        return JsonResponse({
            'success': True,
            'est_actif': contenu.est_actif
        })
    
    return JsonResponse({'success': False}, status=400)

  