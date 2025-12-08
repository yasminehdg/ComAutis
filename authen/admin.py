from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile

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
        """Action pour approuver les éducateurs en attente"""
        count = 0
        for profile in queryset:
            if profile.user_type == 'educator' and not profile.user.is_active:
                profile.user.is_active = True
                profile.user.save()
                count += 1
        
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