# ========================================
# FICHIER: paiement/views.py
# ========================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JeuPremium, PaiementJeu, AccesJeu, Level, Subscription
from authen.models import Enfant  # ✅ AJOUTÉ
import uuid
from datetime import datetime


# ========================================
# ANCIENNES VUES (ABONNEMENTS)
# ========================================

@login_required
def level_list(request):
    """Liste des niveaux d'abonnement"""
    levels = Level.objects.all()
    return render(request, 'paiement/levels.html', {'levels': levels})


@login_required
def subscribe(request, level_id):
    """Page d'abonnement"""
    level = get_object_or_404(Level, id=level_id)
    return render(request, 'paiement/subscribe.html', {'level': level})


@login_required
def process_payment(request, level_id):
    """Traitement du paiement d'abonnement"""
    if request.method == 'POST':
        level = get_object_or_404(Level, id=level_id)
        
        # Créer l'abonnement
        Subscription.objects.create(
            parent=request.user,
            level=level,
            active=True,
            simulated_payment_id=str(uuid.uuid4())
        )
        
        messages.success(request, f"Abonnement {level.name} activé avec succès !")
        return redirect('dashboard')
    
    return redirect('paiement:levels')


@login_required
def my_subscriptions(request):
    """Mes abonnements"""
    subscriptions = Subscription.objects.filter(parent=request.user)
    return render(request, 'paiement/my_subscriptions.html', {'subscriptions': subscriptions})


@login_required
def cancel_subscription(request, subscription_id):
    """Annuler un abonnement"""
    subscription = get_object_or_404(Subscription, id=subscription_id, parent=request.user)
    
    if request.method == 'POST':
        subscription.active = False
        subscription.save()
        messages.success(request, "Abonnement annulé avec succès")
        return redirect('paiement:my_subscriptions')
    
    return render(request, 'paiement/cancel_subscription.html', {'subscription': subscription})


@login_required
def change_level(request, current_subscription_id):
    """Changer de niveau d'abonnement"""
    subscription = get_object_or_404(Subscription, id=current_subscription_id, parent=request.user)
    levels = Level.objects.all()
    return render(request, 'paiement/change_level.html', {'subscription': subscription, 'levels': levels})


@login_required
def confirm_level_change(request, subscription_id, new_level_id):
    """Confirmer le changement de niveau"""
    subscription = get_object_or_404(Subscription, id=subscription_id, parent=request.user)
    new_level = get_object_or_404(Level, id=new_level_id)
    
    if request.method == 'POST':
        subscription.level = new_level
        subscription.save()
        messages.success(request, f"Abonnement changé vers {new_level.name}")
        return redirect('paiement:my_subscriptions')
    
    return render(request, 'paiement/confirm_level_change.html', {
        'subscription': subscription,
        'new_level': new_level
    })


# ========================================
# NOUVELLES VUES (JEUX PREMIUM)
# ========================================

@login_required
def verifier_acces_jeu(request, jeu_code):
    """Vérifie si l'utilisateur a accès à un jeu premium"""
    
    # Vérifier si le jeu est premium
    try:
        jeu = JeuPremium.objects.get(jeu_code=jeu_code, actif=True)
    except JeuPremium.DoesNotExist:
        # Le jeu n'est pas premium ou n'existe pas, accès libre
        return True
    
    # Vérifier si l'utilisateur a acheté ce jeu
    acces = AccesJeu.objects.filter(
        parent=request.user,
        jeu_premium=jeu,
        actif=True
    ).exists()
    
    return acces


@login_required
def page_paiement(request, jeu_code):
    """Page de paiement pour un jeu premium"""
    
    # Récupérer le jeu premium
    jeu = get_object_or_404(JeuPremium, jeu_code=jeu_code, actif=True)
    
    # ✅ CORRIGÉ : Récupérer l'enfant sélectionné (dernier enfant ou premier enfant)
    enfants = Enfant.objects.filter(parent=request.user)
    if not enfants.exists():
        messages.error(request, "Vous devez d'abord créer un profil enfant.")
        return redirect('profil_famille')
    
    # Prendre le premier enfant par défaut
    enfant = enfants.first()
    
    # Vérifier si déjà acheté
    deja_achete = AccesJeu.objects.filter(
        parent=request.user,
        jeu_premium=jeu,
        actif=True
    ).exists()
    
    if deja_achete:
        messages.info(request, f"Vous avez déjà accès à {jeu.nom} !")
        return redirect('liste_jeux', enfant_id=enfant.id)
    
    context = {
        'jeu': jeu,
        'enfant': enfant,  # ✅ AJOUTÉ
    }
    
    return render(request, 'paiement/page_paiement.html', context)


@login_required
def traiter_paiement(request, jeu_code):
    """Traite le paiement et débloque le jeu"""
    
    if request.method != 'POST':
        return redirect('paiement:page_paiement', jeu_code=jeu_code)
    
    # Récupérer le jeu
    jeu = get_object_or_404(JeuPremium, jeu_code=jeu_code, actif=True)
    
    # ✅ CORRIGÉ : Récupérer l'enfant
    enfants = Enfant.objects.filter(parent=request.user)
    if not enfants.exists():
        messages.error(request, "Vous devez d'abord créer un profil enfant.")
        return redirect('profil_famille')
    
    enfant = enfants.first()
    
    # Récupérer les informations de la carte
    numero_carte = request.POST.get('numero_carte', '').replace(' ', '')
    nom_carte = request.POST.get('nom_carte', '')
    date_expiration = request.POST.get('date_expiration', '')
    cvv = request.POST.get('cvv', '')
    
    # ========================================
    # VALIDATION SIMPLE DE LA CARTE
    # ========================================
    
    erreurs = []
    
    # Vérifier le numéro de carte (doit avoir 16 chiffres)
    if not numero_carte.isdigit() or len(numero_carte) != 16:
        erreurs.append("Le numéro de carte doit contenir 16 chiffres")
    
    # Vérifier le nom
    if not nom_carte or len(nom_carte) < 3:
        erreurs.append("Le nom sur la carte est invalide")
    
    # Vérifier la date d'expiration (format MM/YY)
    if '/' not in date_expiration or len(date_expiration.split('/')) != 2:
        erreurs.append("La date d'expiration est invalide (format MM/YY)")
    else:
        mois, annee = date_expiration.split('/')
        try:
            mois = int(mois)
            annee = int(annee) + 2000  # Convertir 25 en 2025
            
            if mois < 1 or mois > 12:
                erreurs.append("Le mois d'expiration est invalide")
            
            # Vérifier que la carte n'est pas expirée
            now = datetime.now()
            if annee < now.year or (annee == now.year and mois < now.month):
                erreurs.append("La carte est expirée")
                
        except ValueError:
            erreurs.append("La date d'expiration est invalide")
    
    # Vérifier le CVV (doit avoir 3 chiffres)
    if not cvv.isdigit() or len(cvv) != 3:
        erreurs.append("Le CVV doit contenir 3 chiffres")
    
    # S'il y a des erreurs, retour à la page de paiement
    if erreurs:
        context = {
            'jeu': jeu,
            'enfant': enfant,  # ✅ AJOUTÉ
            'erreurs': erreurs,
            'numero_carte': numero_carte,
            'nom_carte': nom_carte,
            'date_expiration': date_expiration,
        }
        return render(request, 'paiement/page_paiement.html', context)
    
    # ========================================
    # PAIEMENT RÉUSSI (simulation)
    # ========================================
    
    # Créer un ID de transaction unique
    transaction_id = str(uuid.uuid4())
    
    # Masquer le numéro de carte (garder les 4 derniers chiffres)
    numero_masque = f"**** **** **** {numero_carte[-4:]}"
    
    # Créer l'enregistrement du paiement
    paiement = PaiementJeu.objects.create(
        parent=request.user,
        jeu_premium=jeu,
        montant=jeu.prix,
        statut='reussi',
        numero_carte_masque=numero_masque,
        nom_carte=nom_carte,
        transaction_id=transaction_id,
    )
    
    # Donner l'accès au jeu
    AccesJeu.objects.create(
        parent=request.user,
        jeu_premium=jeu,
        paiement=paiement,
        actif=True,
    )
    
    # Rediriger vers la page de succès
    return redirect('paiement:paiement_succes', jeu_code=jeu_code)


@login_required
def paiement_succes(request, jeu_code):
    """Page de confirmation après paiement réussi"""
    
    jeu = get_object_or_404(JeuPremium, jeu_code=jeu_code)
    
    # Récupérer l'enfant
    enfants = Enfant.objects.filter(parent=request.user)
    if not enfants.exists():
        messages.error(request, "Vous devez d'abord créer un profil enfant.")
        return redirect('profil_famille')
    
    enfant = enfants.first()
    
    # ✅ MAPPER LES CODES JEUX VERS LES NOMS D'URL DJANGO
    mapping_jeux = {
        'memory': 'jeu_memory',
        'compter_10': 'jeu_compter_10',
        'saisons': 'jeu_saisons',
        'puzzle': 'jeu_puzzle',
        'labyrinthe': 'labyrinthe',
        'compter_3': 'jeu_compter_3',
        'couleurs': 'jeu_couleurs',
        'emotions': 'jeu_emotions',
        'memory_fruits': 'jeu_memory_fruits',
        'jours_semaine': 'jeu_jours_semaine',
        'animaux': 'animaux_jeu',
        'fruits': 'jeu_fruits',
        'memory_couleurs': 'jeu_memory_couleurs',
    }
    
    # Obtenir le nom de route Django correspondant
    route_name = mapping_jeux.get(jeu_code, 'liste_jeux')
    
    context = {
        'jeu': jeu,
        'enfant': enfant,
        'route_name': route_name,  # ✅ Passer le nom de route au template
    }
    
    return render(request, 'paiement/paiement_succes.html', context)


@login_required
def mes_jeux_premium(request):
    """Liste des jeux premium achetés par l'utilisateur"""
    
    jeux_achetes = AccesJeu.objects.filter(
        parent=request.user,
        actif=True
    ).select_related('jeu_premium')
    
    context = {
        'jeux_achetes': jeux_achetes,
    }
    
    return render(request, 'paiement/mes_jeux_premium.html', context)