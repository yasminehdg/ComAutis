from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta, datetime
import uuid
from .models import Level, Subscription

def level_list(request):
    """Affiche la liste des niveaux d'abonnement disponibles"""
    levels = Level.objects.all()
    return render(request, 'paiement/levels.html', {'levels': levels})


def subscribe(request, level_id):
    """Gère l'abonnement à un niveau"""
    level = get_object_or_404(Level, id=level_id)
    
    # Vérifie si l'utilisateur est déjà abonné à ce niveau
    if Subscription.objects.filter(parent=request.user, level=level, active=True).exists():
        return render(request, 'paiement/already_subscribed.html', {'level': level})
    
    # Si gratuit, crée directement l'abonnement
    if level.price == 0:
        Subscription.objects.create(
            parent=request.user,
            level=level,
            active=True
        )
        return render(request, 'paiement/subscribed.html', {'level': level})
    
    # Si payant, redirige vers page de paiement simulé
    return render(request, 'paiement/pay_level.html', {'level': level})


def process_payment(request, level_id):
    """Traite le paiement d'un abonnement"""
    if request.method == 'POST':
        level = get_object_or_404(Level, id=level_id)
        
        payment_method = request.POST.get('payment_method', 'card')
        
        # Validation pour paiement par carte UNIQUEMENT
        if payment_method == 'card':
            card_number = request.POST.get('card_number', '').replace(' ', '')
            expiry = request.POST.get('expiry', '')
            cvv = request.POST.get('cvv', '')
            card_name = request.POST.get('card_name', '')
            
            # Validations basiques
            errors = []
            
            if len(card_number) != 16 or not card_number.isdigit():
                errors.append('Numéro de carte invalide (16 chiffres requis)')
            
            # Vérifier que la carte commence par 3, 4, 5 ou 6
            if card_number and card_number[0] not in ['3', '4', '5', '6']:
                errors.append('Type de carte non supporté (doit commencer par 3, 4, 5 ou 6)')
            
            if not expiry or len(expiry) != 5 or '/' not in expiry:
                errors.append('Date d\'expiration invalide (format MM/AA requis)')
            else:
                try:
                    month, year = expiry.split('/')
                    month_int = int(month)
                    year_int = int(year)
                    
                    current_year = datetime.now().year % 100
                    current_month = datetime.now().month
                    
                    if month_int < 1 or month_int > 12:
                        errors.append('Mois invalide (doit être entre 01 et 12)')
                    elif year_int < current_year or (year_int == current_year and month_int < current_month):
                        errors.append('Carte expirée')
                except:
                    errors.append('Format de date invalide')
            
            if len(cvv) != 3 or not cvv.isdigit():
                errors.append('CVV invalide (doit contenir 3 chiffres)')
            
            if len(card_name.strip()) < 3:
                errors.append('Nom invalide (minimum 3 caractères)')
            
            # Si des erreurs, retourner au formulaire
            if errors:
                return render(request, 'paiement/pay_level.html', {
                    'level': level,
                    'errors': errors
                })
        
        # Simulation du paiement réussi
        fake_payment_id = str(uuid.uuid4())
        
        # Créer l'abonnement
        Subscription.objects.create(
            parent=request.user,
            level=level,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            active=True,
            simulated_payment_id=fake_payment_id
        )
        
        # Nom du mode de paiement pour l'affichage
        payment_method_name = {
            'card': 'Carte Bancaire',
            'paypal': 'PayPal',
            'mobile': 'Paiement Mobile'
        }.get(payment_method, 'Carte Bancaire')
        
        return render(request, 'paiement/payment_success.html', {
            'level': level,
            'payment_id': fake_payment_id,
            'payment_method': payment_method,
            'payment_method_name': payment_method_name
        })
    
    return redirect('paiement:levels')


def my_subscriptions(request):
    """Affiche tous les abonnements de l'utilisateur"""
    active_subscriptions = Subscription.objects.filter(
        parent=request.user, 
        active=True
    ).select_related('level')
    
    inactive_subscriptions = Subscription.objects.filter(
        parent=request.user, 
        active=False
    ).select_related('level').order_by('-start_date')[:5]  # Les 5 derniers
    
    return render(request, 'paiement/my_subscriptions.html', {
        'active_subscriptions': active_subscriptions,
        'inactive_subscriptions': inactive_subscriptions,
    })


def cancel_subscription(request, subscription_id):
    """Annuler un abonnement"""
    subscription = get_object_or_404(
        Subscription, 
        id=subscription_id, 
        parent=request.user,
        active=True
    )
    
    if request.method == 'POST':
        subscription.active = False
        subscription.end_date = timezone.now()
        subscription.save()
        return redirect('paiement:my_subscriptions')
    
    return render(request, 'paiement/cancel_subscription.html', {
        'subscription': subscription
    })


def change_level(request, current_subscription_id):
    """Changer de niveau d'abonnement"""
    current_subscription = get_object_or_404(
        Subscription, 
        id=current_subscription_id, 
        parent=request.user,
        active=True
    )
    
    # Récupérer tous les autres niveaux disponibles
    available_levels = Level.objects.exclude(id=current_subscription.level.id)
    
    return render(request, 'paiement/change_level.html', {
        'current_subscription': current_subscription,
        'available_levels': available_levels,
    })


def confirm_level_change(request, subscription_id, new_level_id):
    """Confirmer le changement de niveau"""
    if request.method == 'POST':
        # Annuler l'ancien abonnement
        old_subscription = get_object_or_404(
            Subscription, 
            id=subscription_id, 
            parent=request.user,
            active=True
        )
        old_subscription.active = False
        old_subscription.end_date = timezone.now()
        old_subscription.save()
        
        # Créer le nouveau
        new_level = get_object_or_404(Level, id=new_level_id)
        
        # Si gratuit, créer directement
        if new_level.price == 0:
            Subscription.objects.create(
                parent=request.user,
                level=new_level,
                active=True
            )
            return render(request, 'paiement/level_changed.html', {
                'new_level': new_level
            })
        else:
            # Si payant, rediriger vers paiement
            return render(request, 'paiement/pay_level.html', {
                'level': new_level,
                'is_change': True
            })
    
    return redirect('paiement:my_subscriptions')