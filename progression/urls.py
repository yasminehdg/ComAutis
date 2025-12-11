from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # ========================================
    # DASHBOARD ADMIN
    # ========================================
    path('admin-dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('admin/valider-educateur/<int:educateur_id>/', views.admin_valider_educateur, name='admin_valider_educateur'),
    path('admin/desactiver-educateur/<int:educateur_id>/', views.admin_desactiver_educateur, name='admin_desactiver_educateur'),
    path('admin/statistiques/', views.admin_statistiques_globales, name='admin_statistiques'),
    path('admin/gestion-educateurs/', views.admin_gestion_educateurs, name='admin_gestion_educateurs'),
    # ✨ NOUVELLE URL : Point d'entrée principal depuis le dashboard
    path('', views.dashboard_progression, name='dashboard_progression'),
    
    # Page principale de progression
    path('enfant/', views.progression_enfant, name='progression_enfant'),
    path('enfant/<int:enfant_id>/', views.progression_enfant, name='progression_enfant_detail'),
    
    # Liste de tous les enfants
    path('liste/', views.liste_enfants, name='liste_enfants'),
    
    # Dashboards
    path('parent/', views.dashboard_parent, name='dashboard_parent'),
    path('educateur/', views.dashboard_educateur, name='dashboard_educateur'),
    path('educateur/enfant/<int:enfant_id>/', views.detail_enfant_educateur, name='detail_enfant_educateur'),
    
    # Actions
    path('terminer-activite/<int:enfant_id>/', views.terminer_activite, name='terminer_activite'),
    path('reinitialiser/<int:enfant_id>/', views.reinitialiser_progression, name='reinitialiser_progression'),
    
    # Vue de test pour simuler une activité
    path('simuler/<int:enfant_id>/', views.simuler_activite, name='simuler_activite'),
    
    # Gestion des enfants par l'éducateur
    path('educateur/gerer-enfants/', views.gerer_enfants_educateur, name='gerer_enfants_educateur'),
    path('educateur/ajouter-enfant/<int:enfant_id>/', views.ajouter_enfant_educateur, name='ajouter_enfant_educateur'),
    path('educateur/retirer-enfant/<int:enfant_id>/', views.retirer_enfant_educateur, name='retirer_enfant_educateur'),


]


urlpatterns += [
    
    # ============================================
    # GESTION DES CONTENUS
    # ============================================
    
    # Liste et gestion
    path('contenus/', views.gestion_contenus, name='gestion_contenus'),
    path('contenus/creer/', views.creer_contenu, name='creer_contenu'),
    path('contenus/<int:contenu_id>/', views.detail_contenu, name='detail_contenu'),
    path('contenus/<int:contenu_id>/modifier/', views.modifier_contenu, name='modifier_contenu'),
    path('contenus/<int:contenu_id>/supprimer/', views.supprimer_contenu, name='supprimer_contenu'),
    path('contenus/<int:contenu_id>/valider/', views.valider_contenu, name='valider_contenu'),
    path('contenus/<int:contenu_id>/dupliquer/', views.dupliquer_contenu, name='dupliquer_contenu'),
    
    # ============================================
    # GESTION DES CATÉGORIES
    # ============================================
    
    path('categories/', views.gestion_categories, name='gestion_categories'),
    path('categories/creer/', views.creer_categorie, name='creer_categorie'),
    path('categories/<int:categorie_id>/modifier/', views.modifier_categorie, name='modifier_categorie'),
    
    # ============================================
    # ASSIGNATION AUX NIVEAUX
    # ============================================
    
    path('niveaux-contenus/', views.gestion_niveaux_contenus, name='gestion_niveaux_contenus'),
    path('niveaux-contenus/assigner/', views.assigner_contenu_niveau, name='assigner_contenu_niveau'),
    
    # ============================================
    # ÉVALUATIONS
    # ============================================
    
    path('contenus/<int:contenu_id>/evaluer/', views.evaluer_contenu, name='evaluer_contenu'),
    
    # ============================================
    # BIBLIOTHÈQUE (CÔTÉ ENFANT)
    # ============================================
    
    path('bibliotheque/', views.bibliotheque_contenus, name='bibliotheque_contenus'),
    path('bibliotheque/<int:enfant_id>/', views.bibliotheque_contenus, name='bibliotheque_contenus_enfant'),
    path('contenu/<int:contenu_id>/jouer/<int:enfant_id>/', views.jouer_contenu, name='jouer_contenu'),
    
    # ============================================
    # API AJAX
    # ============================================
    
    path('api/contenu/<int:contenu_id>/toggle-actif/', views.toggle_contenu_actif, name='toggle_contenu_actif'),
]
