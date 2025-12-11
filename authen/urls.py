from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),           # accueil
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil-famille/', views.profil_famille, name='profil_famille'),
    path('ajouter-enfant/', views.ajouter_enfant, name='ajouter_enfant'),
    path('modifier-enfant/<int:enfant_id>/', views.modifier_enfant, name='modifier_enfant'),
    path('supprimer-enfant/<int:enfant_id>/', views.supprimer_enfant, name='supprimer_enfant'),
    path('selection-enfant/', views.selection_enfant, name='selection_enfant'),
    path('enfant/<int:enfant_id>/dashboard/', views.dashboard_enfant, name='dashboard_enfant'),
    path('users/', views.users_list, name='users_list'),
    path('jeux/', views.liste_jeux, name='liste_jeux'),
    path('jeux/memory/', views.jeu_memory, name='jeu_memory'),
    path('jeux/compter-3/', views.jeu_compter_3, name='jeu_compter_3'),
    path('jeux/couleurs/', views.jeu_couleurs, name='jeu_couleurs'),
    path('jeux/emotions/', views.jeu_emotions, name='jeu_emotions'),
    path('jeux/compter-10/', views.jeu_compter_10, name='jeu_compter_10'),
    path('jeux/memory-fruits/', views.jeu_memory_fruits, name='jeu_memory_fruits'),
    path('jeux/jours-semaine/', views.jeu_jours_semaine, name='jeu_jours_semaine'),
    # Jeu animaux
    path('jeux/animaux/', views.animaux_jeu, name='animaux_jeu'),
    path('jeux/fruits/', views.jeu_fruits, name='jeu_fruits'),
    path('jeux/memory-couleurs/', views.jeu_memory_couleurs, name='jeu_memory_couleurs'),
    path('jeux/saisons/', views.jeu_saisons, name='jeu_saisons'),
    path('jeux/puzzle/', views.jeu_puzzle, name='jeu_puzzle'),
    path('jeux/labyrinthe/', views.labyrinthe_jeu, name='labyrinthe'),
    path('sons/', views.page_sons, name='page_sons'),
    path('enfant/<int:enfant_id>/pictogrammes/', views.pictogrammes_view, name='pictogrammes'),
    path('enfant/<int:enfant_id>/dessiner/', views.dessiner_view, name='dessiner'),
    path('enfant/<int:enfant_id>/videos/', views.videos_view, name='videos'),
    path('enfant/<int:enfant_id>/histoires/', views.histoires_view, name='histoires'),
    path('ressources/', views.ressources, name='ressources'),
    path('parametres/', views.parametres, name='parametres'),
    # Badges et Notifications
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),

]


