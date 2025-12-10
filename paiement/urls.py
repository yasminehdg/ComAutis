from django.urls import path
from . import views

app_name = 'paiement'

urlpatterns = [
    # Niveaux & Abonnement
    path('levels/', views.level_list, name='levels'),
    path('subscribe/<int:level_id>/', views.subscribe, name='subscribe'),
    path('subscribe/<int:level_id>/process/', views.process_payment, name='process_payment'),

    # Gestion des abonnements
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscription/<int:subscription_id>/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/<int:current_subscription_id>/change/', views.change_level, name='change_level'),
    path('subscription/<int:subscription_id>/change/<int:new_level_id>/confirm/', views.confirm_level_change, name='confirm_level_change'),
]