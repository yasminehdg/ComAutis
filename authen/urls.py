from django.urls import path
from . import views
from .admin_views import (
    admin_dashboard,
    admin_users_list,
    admin_user_detail,
    admin_approve_educator,
    admin_deactivate_user,
    admin_delete_user,
    admin_enfants_list,
    admin_forum_moderation,
    admin_delete_topic,
    admin_delete_post,
    admin_subscriptions,
    admin_statistics,
)

urlpatterns = [
    # ========== PAGES PRINCIPALES ==========
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ========== GESTION FAMILLE ==========
    path('profil-famille/', views.profil_famille, name='profil_famille'),
    path('ajouter-enfant/', views.ajouter_enfant, name='ajouter_enfant'),
    path('modifier-enfant/<int:enfant_id>/', views.modifier_enfant, name='modifier_enfant'),
    path('supprimer-enfant/<int:enfant_id>/', views.supprimer_enfant, name='supprimer_enfant'),
    path('selection-enfant/', views.selection_enfant, name='selection_enfant'),
    path('enfant/<int:enfant_id>/dashboard/', views.dashboard_enfant, name='dashboard_enfant'),
    
    # ========== 🎮 JEUX AVEC TRACKING - NOUVELLE STRUCTURE ==========
    path('enfant/<int:enfant_id>/jeux/', views.liste_jeux, name='liste_jeux'),
    path('enfant/<int:enfant_id>/jeux/memory/', views.jeu_memory, name='jeu_memory'),
    path('enfant/<int:enfant_id>/jeux/compter-3/', views.jeu_compter_3, name='jeu_compter_3'),
    path('enfant/<int:enfant_id>/jeux/couleurs/', views.jeu_couleurs, name='jeu_couleurs'),
    path('enfant/<int:enfant_id>/jeux/emotions/', views.jeu_emotions, name='jeu_emotions'),
    path('enfant/<int:enfant_id>/jeux/compter-10/', views.jeu_compter_10, name='jeu_compter_10'),
    path('enfant/<int:enfant_id>/jeux/memory-fruits/', views.jeu_memory_fruits, name='jeu_memory_fruits'),
    path('enfant/<int:enfant_id>/jeux/jours-semaine/', views.jeu_jours_semaine, name='jeu_jours_semaine'),
    path('enfant/<int:enfant_id>/jeux/animaux/', views.animaux_jeu, name='animaux_jeu'),
    path('enfant/<int:enfant_id>/jeux/fruits/', views.jeu_fruits, name='jeu_fruits'),
    path('enfant/<int:enfant_id>/jeux/memory-couleurs/', views.jeu_memory_couleurs, name='jeu_memory_couleurs'),
    path('enfant/<int:enfant_id>/jeux/saisons/', views.jeu_saisons, name='jeu_saisons'),
    path('enfant/<int:enfant_id>/jeux/puzzle/', views.jeu_puzzle, name='jeu_puzzle'),
    path('enfant/<int:enfant_id>/jeux/labyrinthe/', views.labyrinthe_jeu, name='labyrinthe'),
    
    # ========== ACTIVITÉS ENFANT (AVEC TRACKING) ==========
    path('enfant/<int:enfant_id>/sons/', views.page_sons, name='page_sons'),
    path('enfant/<int:enfant_id>/pictogrammes/', views.pictogrammes_view, name='pictogrammes'),
    path('enfant/<int:enfant_id>/dessiner/', views.dessiner_view, name='dessiner'),
    path('enfant/<int:enfant_id>/videos/', views.videos_view, name='videos'),
    path('enfant/<int:enfant_id>/histoires/', views.histoires_view, name='histoires'),
    
    # ========== RESSOURCES ET PARAMÈTRES ==========
    path('ressources/', views.ressources, name='ressources'),
    path('parametres/', views.parametres, name='parametres'),
    path('progression/', views.progression, name='progression'),
    
    # ========== BADGES ET NOTIFICATIONS ==========
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # ========== ✨ ÉDUCATEUR ==========
    path('educateur/enfant/<int:enfant_id>/', views.educateur_enfant_detail, name='educateur_enfant_detail'),
    path('educateur/enfant/<int:enfant_id>/observation/', views.educateur_ajouter_observation, name='educateur_ajouter_observation'),
    
    # ========== ✨ PARENT - OBSERVATIONS ==========
    path('enfant/<int:enfant_id>/observations/', views.parent_voir_observations, name='parent_voir_observations'),
    
    # ========== ADMIN DASHBOARD ==========
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/users/', admin_users_list, name='admin_users_list'),
    path('admin-dashboard/users/<int:user_id>/', admin_user_detail, name='admin_user_detail'),
    path('admin-dashboard/users/<int:user_id>/approve/', admin_approve_educator, name='admin_approve_educator'),
    path('admin-dashboard/users/<int:user_id>/deactivate/', admin_deactivate_user, name='admin_deactivate_user'),
    path('admin-dashboard/users/<int:user_id>/delete/', admin_delete_user, name='admin_delete_user'),
    path('admin-dashboard/enfants/', admin_enfants_list, name='admin_enfants_list'),
    path('admin-dashboard/forum/', admin_forum_moderation, name='admin_forum_moderation'),
    path('admin-dashboard/forum/topic/<int:topic_id>/delete/', admin_delete_topic, name='admin_delete_topic'),
    path('admin-dashboard/forum/post/<int:post_id>/delete/', admin_delete_post, name='admin_delete_post'),
    path('admin-dashboard/subscriptions/', admin_subscriptions, name='admin_subscriptions'),
    path('admin-dashboard/statistics/', admin_statistics, name='admin_statistics'),
    
    # ========== API ENDPOINTS ==========
    path('api/modifier-profil/', views.modifier_profil, name='modifier_profil'),
    path('api/changer-mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),
    path('api/upload-photo-profil/', views.upload_photo_profil, name='upload_photo_profil'),
    path('api/supprimer-enfant/<int:enfant_id>/', views.supprimer_enfant, name='supprimer_enfant'),
    path('api/supprimer-compte/', views.supprimer_compte, name='supprimer_compte'),
    
    path('users/', views.users_list, name='users_list'),

    # 🎮 API Tracking Activités
    path('api/start-activity/', views.start_activity_api, name='start_activity_api'),
    path('api/end-activity/', views.end_activity_api, name='end_activity_api'),
]