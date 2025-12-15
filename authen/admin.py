from django.contrib import admin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile, EducateurEnfant, ObservationEducateur

# Personnaliser l'affichage des profils utilisateurs
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone', 'institution', 'created_at', 'is_user_active')
    list_filter = ('user_type', 'created_at', 'user__is_active')
    search_fields = ('user__username', 'user__email', 'phone', 'institution')
    ordering = ('-created_at',)
    
    def is_user_active(self, obj):
        return "✅ Actif" if obj.user.is_active else "⏳ En attente"
    is_user_active.short_description = "Statut"
    
    actions = ['approve_educators']
    
    def approve_educators(self, request, queryset):
        """Action pour approuver les éducateurs en attente + ENVOI EMAIL"""
        count = 0
        for profile in queryset:
            if profile.user_type == 'educator' and not profile.user.is_active:
                profile.user.is_active = True
                profile.user.save()
                count += 1
                
                # 🆕 ENVOI D'EMAIL AUTOMATIQUE
                try:
                    subject = "✅ Votre compte ComAutiste a été approuvé !"
                    message = f"""
Bonjour {profile.user.first_name or profile.user.username},

Bonne nouvelle ! 🎉

Votre compte éducateur sur ComAutiste a été approuvé par notre équipe.

Vous pouvez maintenant vous connecter à votre espace :
👉 https://votre-site.com/login/

Vos identifiants :
📧 Nom d'utilisateur : {profile.user.username}
🔐 Mot de passe : celui que vous avez choisi lors de l'inscription

Une fois connecté, vous pourrez :
✅ Suivre les enfants qui vous sont assignés
✅ Consulter leurs activités et progrès
✅ Ajouter des observations
✅ Accéder aux ressources pédagogiques

Si vous avez des questions, n'hésitez pas à nous contacter.

Bienvenue dans l'équipe ComAutiste ! 🌟

---
L'équipe ComAutiste
support@comautiste.fr
                    """
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[profile.user.email],
                        fail_silently=False,
                    )
                    
                    self.message_user(request, f"✅ {profile.user.username} approuvé et email envoyé !")
                    
                except Exception as e:
                    self.message_user(request, f"⚠️ {profile.user.username} approuvé mais erreur email : {str(e)}")
        
        if count == 0:
            self.message_user(request, "Aucun éducateur à approuver parmi la sélection.")
        else:
            self.message_user(request, f"{count} éducateur(s) approuvé(s) avec succès !")
    
    approve_educators.short_description = "✅ Approuver les éducateurs sélectionnés"

# Enregistrer le modèle UserProfile
admin.site.register(UserProfile, UserProfileAdmin)


# Personnaliser l'affichage des utilisateurs dans l'admin
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'date_joined', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name')
    ordering = ('-date_joined',)
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Utilisateurs activés avec succès !")
    activate_users.short_description = "✅ Activer les utilisateurs sélectionnés"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Utilisateurs désactivés avec succès !")
    deactivate_users.short_description = "❌ Désactiver les utilisateurs sélectionnés"

# Désenregistrer le modèle User par défaut et enregistrer notre version personnalisée
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ========================================
# ✨ ADMINS POUR LES ÉDUCATEURS
# ========================================

@admin.register(EducateurEnfant)
class EducateurEnfantAdmin(admin.ModelAdmin):
    list_display = ('educateur', 'enfant', 'date_ajout', 'statut')
    list_filter = ('statut', 'date_ajout')
    search_fields = ('educateur__username', 'enfant__prenom', 'enfant__nom')
    ordering = ('-date_ajout',)
    
    fieldsets = (
        ('👨‍🏫 Relation Éducateur-Enfant', {
            'fields': ('educateur', 'enfant', 'statut')
        }),
        ('📝 Notes et Objectifs', {
            'fields': ('notes_privees', 'objectifs'),
            'classes': ('collapse',),
            'description': 'Notes privées de l\'éducateur (non visibles par le parent)'
        }),
    )
    
    # Filtrer pour afficher seulement les éducateurs
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "educateur":
            kwargs["queryset"] = User.objects.filter(profile__user_type='educator', is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    actions = ['archiver_relations', 'reactiver_relations']
    
    def archiver_relations(self, request, queryset):
        """Archiver les relations sélectionnées"""
        queryset.update(statut='archive')
        self.message_user(request, "Relations archivées avec succès !")
    archiver_relations.short_description = "📦 Archiver les relations sélectionnées"
    
    def reactiver_relations(self, request, queryset):
        """Réactiver les relations archivées"""
        queryset.update(statut='actif')
        self.message_user(request, "Relations réactivées avec succès !")
    reactiver_relations.short_description = "✅ Réactiver les relations sélectionnées"


@admin.register(ObservationEducateur)
class ObservationEducateurAdmin(admin.ModelAdmin):
    list_display = ('titre', 'enfant', 'educateur', 'type_observation', 'visible_parent', 'date_observation')
    list_filter = ('type_observation', 'visible_parent', 'date_observation')
    search_fields = ('titre', 'description', 'enfant__prenom', 'educateur__username')
    ordering = ('-date_observation',)
    
    fieldsets = (
        ('📝 Observation', {
            'fields': ('educateur', 'enfant', 'titre', 'description', 'type_observation')
        }),
        ('👁️ Visibilité', {
            'fields': ('visible_parent',),
            'description': 'Cochez si le parent peut voir cette observation'
        }),
    )
    
    # Filtrer pour afficher seulement les éducateurs
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "educateur":
            kwargs["queryset"] = User.objects.filter(profile__user_type='educator', is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    actions = ['rendre_visible', 'rendre_invisible']
    
    def rendre_visible(self, request, queryset):
        """Rendre les observations visibles aux parents"""
        queryset.update(visible_parent=True)
        self.message_user(request, "Observations rendues visibles aux parents !")
    rendre_visible.short_description = "👁️ Rendre visible aux parents"
    
    def rendre_invisible(self, request, queryset):
        """Rendre les observations invisibles aux parents"""
        queryset.update(visible_parent=False)
        self.message_user(request, "Observations rendues privées !")
    rendre_invisible.short_description = "🔒 Rendre privé"