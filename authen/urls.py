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
    # Badges et Notifications
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),

]


