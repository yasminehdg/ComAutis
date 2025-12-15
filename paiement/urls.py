# ========================================
# FICHIER: paiement/urls.py
# ========================================

from django.urls import path
from . import views

app_name = 'paiement'

urlpatterns = [
    # ===== ANCIENNES URLS (ABONNEMENTS) =====
    path('levels/', views.level_list, name='levels'),
    path('subscribe/<int:level_id>/', views.subscribe, name='subscribe'),
    path('subscribe/<int:level_id>/process/', views.process_payment, name='process_payment'),
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscription/<int:subscription_id>/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/<int:current_subscription_id>/change/', views.change_level, name='change_level'),
    path('subscription/<int:subscription_id>/change/<int:new_level_id>/confirm/', views.confirm_level_change, name='confirm_level_change'),
    
    # ===== NOUVELLES URLS (JEUX PREMIUM) =====
    path('jeu/<str:jeu_code>/payer/', views.page_paiement, name='page_paiement'),
    path('jeu/<str:jeu_code>/traiter/', views.traiter_paiement, name='traiter_paiement'),
    path('jeu/<str:jeu_code>/succes/', views.paiement_succes, name='paiement_succes'),
    path('mes-jeux/', views.mes_jeux_premium, name='mes_jeux_premium'),
]