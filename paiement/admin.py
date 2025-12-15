# ========================================
# FICHIER: paiement/admin.py
# ========================================

from django.contrib import admin
from .models import Level, Subscription, JeuPremium, PaiementJeu, AccesJeu

# ===== MODÈLES EXISTANTS =====

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
    search_fields = ('name',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('parent', 'level', 'start_date', 'end_date', 'active')
    list_filter = ('active', 'level')
    search_fields = ('parent__username',)


# ===== NOUVEAUX MODÈLES JEUX PREMIUM =====

@admin.register(JeuPremium)
class JeuPremiumAdmin(admin.ModelAdmin):
    list_display = ('nom', 'jeu_code', 'prix', 'icone', 'actif', 'created_at')
    list_filter = ('actif',)
    search_fields = ('nom', 'jeu_code')
    list_editable = ('prix', 'actif')

@admin.register(PaiementJeu)
class PaiementJeuAdmin(admin.ModelAdmin):
    list_display = ('parent', 'jeu_premium', 'montant', 'statut', 'date_paiement')
    list_filter = ('statut', 'date_paiement')
    search_fields = ('parent__username', 'transaction_id')
    readonly_fields = ('transaction_id', 'date_paiement')

@admin.register(AccesJeu)
class AccesJeuAdmin(admin.ModelAdmin):
    list_display = ('parent', 'jeu_premium', 'date_achat', 'actif')
    list_filter = ('actif', 'date_achat')
    search_fields = ('parent__username', 'jeu_premium__nom')