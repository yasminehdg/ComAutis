from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import (
    EnfantProgression, HistoriqueActivite, Badge, BadgeObtenu,
    Categorie, Contenu, EvaluationContenu, NiveauContenu
)

# ============================================
# ENFANT PROGRESSION ADMIN
# ============================================

@admin.register(EnfantProgression)
class EnfantProgressionAdmin(admin.ModelAdmin):
    list_display = [
        'nom_enfant', 
        'niveau', 
        'score', 
        'activites_terminees',
        'activites_totales',
        'afficher_pourcentage',
        'date_modification'
    ]
    
    list_filter = ['niveau', 'date_creation']
    search_fields = ['nom_enfant']
    readonly_fields = ['date_creation', 'date_modification', 'afficher_pourcentage']
    
    fieldsets = (
        ('👤 Informations de l\'enfant', {
            'fields': ('nom_enfant',)
        }),
        ('📊 Progression', {
            'fields': (
                'niveau', 
                'score', 
                'activites_terminees', 
                'activites_totales',
                'afficher_pourcentage'
            )
        }),
        ('📅 Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def afficher_pourcentage(self, obj):
        """Affiche le pourcentage de progression dans l'admin"""
        pourcentage = obj.pourcentage_progression()
        return f"{pourcentage}%"
    afficher_pourcentage.short_description = "Progression"
    
    actions = ['reinitialiser_progression', 'ajouter_100_points']
    
    def reinitialiser_progression(self, request, queryset):
        """Action pour réinitialiser la progression des enfants sélectionnés"""
        for enfant in queryset:
            enfant.niveau = 1
            enfant.score = 0
            enfant.activites_terminees = 0
            enfant.activites_totales = 10
            enfant.save()
        self.message_user(request, f"{queryset.count()} progression(s) réinitialisée(s)")
    reinitialiser_progression.short_description = "🔄 Réinitialiser la progression"
    
    def ajouter_100_points(self, request, queryset):
        """Action pour ajouter 100 points aux enfants sélectionnés"""
        for enfant in queryset:
            enfant.terminer_activite(points=100)
        self.message_user(request, f"100 points ajoutés à {queryset.count()} enfant(s)")
    ajouter_100_points.short_description = "⭐ Ajouter 100 points"


# ============================================
# HISTORIQUE ACTIVITE ADMIN
# ============================================

@admin.register(HistoriqueActivite)
class HistoriqueActiviteAdmin(admin.ModelAdmin):
    list_display = [
        'enfant',
        'type_activite',
        'nom_activite',
        'points_gagnes',
        'afficher_duree',
        'afficher_succes',
        'date_activite'
    ]
    
    list_filter = ['type_activite', 'succes', 'date_activite']
    search_fields = ['enfant__nom_enfant', 'nom_activite']
    readonly_fields = ['date_activite']
    date_hierarchy = 'date_activite'
    
    def afficher_duree(self, obj):
        """Affiche la durée formatée"""
        if obj.duree_minutes:
            return f"{obj.duree_minutes} min"
        return "-"
    afficher_duree.short_description = "Durée"
    
    def afficher_succes(self, obj):
        """Affiche le succès avec un badge coloré"""
        if obj.succes:
            return format_html(
                '<span style="background: #d4edda; color: #155724; padding: 3px 10px; '
                'border-radius: 10px; font-weight: 600;">✅ Réussi</span>'
            )
        return format_html(
            '<span style="background: #f8d7da; color: #721c24; padding: 3px 10px; '
            'border-radius: 10px; font-weight: 600;">❌ Échoué</span>'
        )
    afficher_succes.short_description = "Succès"


# ============================================
# BADGE ADMIN
# ============================================

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = [
        'afficher_badge',
        'nom',
        'type_condition',
        'valeur_requise',
        'points_bonus',
        'nb_obtentions'
    ]
    
    list_filter = ['type_condition', 'est_actif']
    search_fields = ['nom', 'description']
    
    fieldsets = (
        ('🏆 Informations du Badge', {
            'fields': ('nom', 'description', 'icone', 'couleur')
        }),
        ('🎯 Conditions d\'Obtention', {
            'fields': ('type_condition', 'valeur_requise', 'points_bonus')
        }),
        ('⚙️ Options', {
            'fields': ('est_actif',)
        }),
    )
    
    def afficher_badge(self, obj):
        """Affiche le badge avec son icône et sa couleur"""
        couleur = obj.couleur or '#667eea'
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 8px; '
            'background: {}; padding: 5px 15px; border-radius: 20px;">'
            '<span style="font-size: 20px;">{}</span>'
            '<span style="color: white; font-weight: 600;">{}</span>'
            '</div>',
            couleur,
            obj.icone or '🏆',
            obj.nom
        )
    afficher_badge.short_description = "Badge"
    
    def nb_obtentions(self, obj):
        """Nombre de fois que le badge a été obtenu"""
        count = BadgeObtenu.objects.filter(badge=obj).count()
        return f"{count} fois"
    nb_obtentions.short_description = "Obtentions"


# ============================================
# BADGE OBTENU ADMIN
# ============================================

@admin.register(BadgeObtenu)
class BadgeObtenuAdmin(admin.ModelAdmin):
    list_display = ['enfant', 'badge', 'date_obtention']
    list_filter = ['badge', 'date_obtention']
    search_fields = ['enfant__nom_enfant', 'badge__nom']
    readonly_fields = ['date_obtention']
    date_hierarchy = 'date_obtention'


# ============================================
# CATEGORIE ADMIN
# ============================================

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = [
        'afficher_categorie',
        'nom',
        'nb_contenus',
        'ordre_affichage'
    ]
    
    list_editable = ['ordre_affichage']
    search_fields = ['nom', 'description']
    
    fieldsets = (
        ('📁 Informations de la Catégorie', {
            'fields': ('nom', 'description', 'icone', 'couleur')
        }),
        ('⚙️ Affichage', {
            'fields': ('ordre_affichage',)
        }),
    )
    
    def afficher_categorie(self, obj):
        """Affiche la catégorie avec son icône et sa couleur"""
        couleur = obj.couleur or '#3498db'
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 8px; '
            'background: {}; padding: 5px 15px; border-radius: 10px;">'
            '<span style="font-size: 18px;">{}</span>'
            '<span style="color: white; font-weight: 600;">{}</span>'
            '</div>',
            couleur,
            obj.icone or '📁',
            obj.nom
        )
    afficher_categorie.short_description = "Catégorie"
    
    def nb_contenus(self, obj):
        """Nombre de contenus dans cette catégorie"""
        count = Contenu.objects.filter(categorie=obj).count()
        return f"{count} contenu(s)"
    nb_contenus.short_description = "Contenus"


# ============================================
# CONTENU ADMIN
# ============================================

@admin.register(Contenu)
class ContenuAdmin(admin.ModelAdmin):
    list_display = [
        'afficher_type',
        'titre',
        'afficher_categorie_badge',
        'afficher_niveaux',
        'afficher_difficulte',
        'afficher_statut',
        'afficher_stats',
        'date_creation'
    ]
    
    list_filter = [
        'type_contenu',
        'categorie',
        'difficulte',
        'est_actif',
        'est_valide',
        'est_premium',
        'date_creation'
    ]
    
    search_fields = [
        'titre',
        'description',
        'objectif_pedagogique',
        'competences_travaillees',
        'tags'
    ]
    
    readonly_fields = [
        'createur',
        'date_creation',
        'date_modification',
        'modificateur',
        'nb_vues',
        'nb_completions',
        'afficher_note_moyenne',
        'afficher_taux_completion'
    ]
    
    fieldsets = (
        ('📝 Informations Générales', {
            'fields': (
                'titre',
                'description',
                'type_contenu',
                'categorie'
            )
        }),
        ('🎯 Niveaux et Difficulté', {
            'fields': (
                'niveau_min',
                'niveau_max',
                'difficulte',
                'duree_estimee',
                'points_recompense'
            )
        }),
        ('🎓 Pédagogie', {
            'fields': (
                'objectif_pedagogique',
                'competences_travaillees',
                'tags'
            )
        }),
        ('📎 Fichiers', {
            'fields': (
                'fichier',
                'image_preview',
                'url_externe',
                'fichier_solution'
            )
        }),
        ('⚙️ Options', {
            'fields': (
                'est_actif',
                'est_premium',
                'est_valide'
            )
        }),
        ('📊 Statistiques', {
            'fields': (
                'nb_vues',
                'nb_completions',
                'afficher_note_moyenne',
                'afficher_taux_completion'
            ),
            'classes': ('collapse',)
        }),
        ('🔐 Métadonnées', {
            'fields': (
                'createur',
                'date_creation',
                'modificateur',
                'date_modification'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['valider_contenus', 'activer_contenus', 'desactiver_contenus']
    
    def save_model(self, request, obj, form, change):
        """Enregistre le créateur et le modificateur"""
        if not change:
            obj.createur = request.user
        obj.modificateur = request.user
        super().save_model(request, obj, form, change)
    
    def afficher_type(self, obj):
        """Affiche le type avec un badge coloré"""
        types_icons = {
            'jeu': ('🎮', '#3498db'),
            'video': ('🎥', '#e74c3c'),
            'son': ('🎵', '#9b59b6'),
            'coloriage': ('🎨', '#f39c12'),
            'histoire': ('📖', '#2ecc71'),
            'exercice': ('✏️', '#1abc9c'),
        }
        
        icon, color = types_icons.get(obj.type_contenu, ('📄', '#95a5a6'))
        
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; '
            'border-radius: 15px; font-size: 12px; font-weight: 600;">'
            '{} {}</span>',
            color,
            icon,
            obj.get_type_contenu_display()
        )
    afficher_type.short_description = "Type"
    
    def afficher_categorie_badge(self, obj):
        """Affiche la catégorie sous forme de badge"""
        if obj.categorie:
            couleur = obj.categorie.couleur or '#3498db'
            return format_html(
                '<span style="background: {}; color: white; padding: 3px 10px; '
                'border-radius: 10px; font-size: 11px;">{} {}</span>',
                couleur,
                obj.categorie.icone or '📁',
                obj.categorie.nom
            )
        return "-"
    afficher_categorie_badge.short_description = "Catégorie"
    
    def afficher_niveaux(self, obj):
        """Affiche les niveaux"""
        return f"Niv. {obj.niveau_min} - {obj.niveau_max}"
    afficher_niveaux.short_description = "Niveaux"
    
    def afficher_difficulte(self, obj):
        """Affiche la difficulté avec des étoiles"""
        etoiles = '⭐' * obj.difficulte
        return format_html('<span style="font-size: 14px;">{}</span>', etoiles)
    afficher_difficulte.short_description = "Difficulté"
    
    def afficher_statut(self, obj):
        """Affiche le statut avec des badges"""
        badges = []
        
        if obj.est_valide:
            badges.append(
                '<span style="background: #d4edda; color: #155724; padding: 2px 8px; '
                'border-radius: 8px; font-size: 10px; margin-right: 3px;">✅ Validé</span>'
            )
        else:
            badges.append(
                '<span style="background: #fff3cd; color: #856404; padding: 2px 8px; '
                'border-radius: 8px; font-size: 10px; margin-right: 3px;">⏳ En attente</span>'
            )
        
        if not obj.est_actif:
            badges.append(
                '<span style="background: #f8d7da; color: #721c24; padding: 2px 8px; '
                'border-radius: 8px; font-size: 10px; margin-right: 3px;">❌ Inactif</span>'
            )
        
        if obj.est_premium:
            badges.append(
                '<span style="background: #ffd700; color: #000; padding: 2px 8px; '
                'border-radius: 8px; font-size: 10px;">💎 Premium</span>'
            )
        
        return format_html(''.join(badges))
    afficher_statut.short_description = "Statut"
    
    def afficher_stats(self, obj):
        """Affiche les statistiques"""
        return format_html(
            '<div style="font-size: 11px;">'
            '👁️ {} vues<br>'
            '✅ {} complétés'
            '</div>',
            obj.nb_vues,
            obj.nb_completions
        )
    afficher_stats.short_description = "Stats"
    
    def afficher_note_moyenne(self, obj):
        """Affiche la note moyenne"""
        evaluations = EvaluationContenu.objects.filter(contenu=obj)
        if evaluations.exists():
            moyenne = evaluations.aggregate(Avg('note'))['note__avg']
            if moyenne:
                etoiles = '⭐' * int(round(moyenne))
                return format_html(
                    '{} ({:.1f}/5)',
                    etoiles,
                    moyenne
                )
        return "Pas encore évalué"
    afficher_note_moyenne.short_description = "Note moyenne"
    
    def afficher_taux_completion(self, obj):
        """Affiche le taux de complétion"""
        taux = obj.taux_completion()
        
        if taux >= 80:
            color = '#28a745'
        elif taux >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<div style="width: 100px; background: #e0e0e0; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; background: {}; padding: 2px 5px; color: white; '
            'font-size: 10px; font-weight: 600; text-align: center;">{:.0f}%</div>'
            '</div>',
            taux,
            color,
            taux
        )
    afficher_taux_completion.short_description = "Taux de complétion"
    
    # Actions
    def valider_contenus(self, request, queryset):
        """Valider les contenus sélectionnés"""
        updated = queryset.update(est_valide=True)
        self.message_user(request, f"{updated} contenu(s) validé(s)")
    valider_contenus.short_description = "✅ Valider les contenus sélectionnés"
    
    def activer_contenus(self, request, queryset):
        """Activer les contenus sélectionnés"""
        updated = queryset.update(est_actif=True)
        self.message_user(request, f"{updated} contenu(s) activé(s)")
    activer_contenus.short_description = "🟢 Activer les contenus"
    
    def desactiver_contenus(self, request, queryset):
        """Désactiver les contenus sélectionnés"""
        updated = queryset.update(est_actif=False)
        self.message_user(request, f"{updated} contenu(s) désactivé(s)")
    desactiver_contenus.short_description = "🔴 Désactiver les contenus"


# ============================================
# EVALUATION CONTENU ADMIN
# ============================================

@admin.register(EvaluationContenu)
class EvaluationContenuAdmin(admin.ModelAdmin):
    list_display = [
        'contenu',
        'evaluateur',
        'afficher_note',
        'date_evaluation'
    ]
    
    list_filter = ['note', 'date_evaluation']
    search_fields = ['contenu__titre', 'evaluateur__username', 'commentaire']
    readonly_fields = ['date_evaluation']
    date_hierarchy = 'date_evaluation'
    
    def afficher_note(self, obj):
        """Affiche la note avec des étoiles"""
        etoiles = '⭐' * obj.note
        return format_html('<span style="font-size: 16px;">{}</span>', etoiles)
    afficher_note.short_description = "Note"


# ============================================
# NIVEAU CONTENU ADMIN
# ============================================

@admin.register(NiveauContenu)
class NiveauContenuAdmin(admin.ModelAdmin):
    list_display = [
        'contenu',
        'niveau',
        'afficher_obligatoire',
        'ordre_affichage'
    ]
    
    list_filter = ['niveau', 'est_obligatoire']
    list_editable = ['ordre_affichage']
    search_fields = ['contenu__titre']
    
    def afficher_obligatoire(self, obj):
        """Affiche si le contenu est obligatoire"""
        if obj.est_obligatoire:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 10px; font-size: 11px; font-weight: 600;">⭐ Obligatoire</span>'
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">Optionnel</span>'
        )
    afficher_obligatoire.short_description = "Type"
