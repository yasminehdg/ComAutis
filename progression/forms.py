from django import forms
from .models import Contenu, Categorie, HistoriqueActivite, Badge, EvaluationContenu, NiveauContenu

# ============================================
# FORMULAIRES POUR LA GESTION DES CONTENUS
# ============================================

class ContenuForm(forms.ModelForm):
    """Formulaire pour créer/modifier un contenu éducatif"""
    
    class Meta:
        model = Contenu
        fields = [
            'titre', 'description', 'type_contenu', 'categorie',
            'niveau_min', 'niveau_max', 'difficulte', 'duree_estimee',
            'points_recompense', 'objectif_pedagogique', 'competences_travaillees',
            'fichier', 'image_preview', 'url_externe', 'fichier_solution',
            'est_actif', 'est_premium', 'tags'
        ]
        
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du contenu éducatif',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du contenu...'
            }),
            'type_contenu': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-control'
            }),
            'niveau_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20,
                'value': 1
            }),
            'niveau_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20,
                'value': 20
            }),
            'difficulte': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duree_estimee': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Durée en minutes'
            }),
            'points_recompense': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 20
            }),
            'objectif_pedagogique': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Quel est l\'objectif pédagogique de ce contenu ?'
            }),
            'competences_travaillees': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: motricité fine, reconnaissance des couleurs, comptage...'
            }),
            'url_externe': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: couleurs, nombres, animaux (séparés par des virgules)'
            }),
            'est_actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'est_premium': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'titre': '📝 Titre',
            'description': '📄 Description',
            'type_contenu': '🎯 Type de contenu',
            'categorie': '📁 Catégorie',
            'niveau_min': '🎚️ Niveau minimum',
            'niveau_max': '🎚️ Niveau maximum',
            'difficulte': '⭐ Difficulté',
            'duree_estimee': '⏱️ Durée estimée (minutes)',
            'points_recompense': '🎁 Points de récompense',
            'objectif_pedagogique': '🎓 Objectif pédagogique',
            'competences_travaillees': '🧠 Compétences travaillées',
            'fichier': '📎 Fichier du contenu',
            'image_preview': '🖼️ Image de prévisualisation',
            'url_externe': '🔗 URL externe (optionnel)',
            'fichier_solution': '✅ Fichier de solution (pour éducateurs)',
            'est_actif': '✓ Contenu actif',
            'est_premium': '💎 Contenu premium',
            'tags': '🏷️ Tags (séparés par virgules)',
        }
        
        help_texts = {
            'niveau_min': 'Niveau minimum requis pour accéder à ce contenu',
            'niveau_max': 'Niveau maximum pour lequel ce contenu est pertinent',
            'points_recompense': 'Nombre de points accordés lors de la complétion',
            'fichier': 'Téléchargez le fichier principal (image, audio, vidéo, PDF...)',
            'image_preview': 'Image de prévisualisation pour afficher le contenu',
            'url_externe': 'Si le contenu est hébergé sur YouTube, Vimeo, etc.',
            'est_actif': 'Décochez pour rendre le contenu invisible',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        niveau_min = cleaned_data.get('niveau_min')
        niveau_max = cleaned_data.get('niveau_max')
        
        if niveau_min and niveau_max and niveau_min > niveau_max:
            raise forms.ValidationError(
                "Le niveau minimum ne peut pas être supérieur au niveau maximum"
            )
        
        return cleaned_data


class ContenuFiltreForm(forms.Form):
    """Formulaire pour filtrer les contenus"""
    
    type_contenu = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Contenu.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.filter(est_active=True),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    niveau = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrer par niveau'
        })
    )
    
    difficulte = forms.ChoiceField(
        choices=[('', 'Toutes difficultés')] + Contenu.DIFFICULTE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    est_valide = forms.ChoiceField(
        choices=[
            ('', 'Tous'),
            ('1', 'Validés uniquement'),
            ('0', 'Non validés uniquement')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '🔍 Rechercher...'
        })
    )


class CategorieForm(forms.ModelForm):
    """Formulaire pour créer/modifier une catégorie"""
    
    class Meta:
        model = Categorie
        fields = ['nom', 'description', 'icone', 'couleur', 'ordre_affichage', 'est_active']
        
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la catégorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la catégorie...'
            }),
            'icone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emoji ou nom d\'icône (ex: 🎨 ou fa-palette)'
            }),
            'couleur': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'ordre_affichage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'est_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'nom': '📝 Nom',
            'description': '📄 Description',
            'icone': '😊 Icône',
            'couleur': '🎨 Couleur',
            'ordre_affichage': '#️⃣ Ordre d\'affichage',
            'est_active': '✓ Catégorie active',
        }


class BadgeForm(forms.ModelForm):
    """Formulaire pour créer/modifier un badge"""
    
    class Meta:
        model = Badge
        fields = [
            'nom', 'description', 'icone', 'condition_type',
            'condition_valeur', 'condition_details', 'couleur_fond',
            'ordre_affichage', 'est_actif'
        ]
        
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du badge'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du badge...'
            }),
            'icone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emoji (ex: 🏆, 🎖️, ⭐)'
            }),
            'condition_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'condition_valeur': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'condition_details': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Détails supplémentaires (optionnel)'
            }),
            'couleur_fond': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'ordre_affichage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'est_actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class EvaluationContenuForm(forms.ModelForm):
    """Formulaire pour évaluer un contenu"""
    
    class Meta:
        model = EvaluationContenu
        fields = ['note', 'commentaire']
        
        widgets = {
            'note': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre commentaire (optionnel)...'
            }),
        }
        
        labels = {
            'note': '⭐ Note',
            'commentaire': '💬 Commentaire',
        }


class NiveauContenuForm(forms.ModelForm):
    """Formulaire pour assigner un contenu à un niveau"""
    
    class Meta:
        model = NiveauContenu
        fields = ['niveau', 'contenu', 'est_obligatoire', 'ordre_dans_niveau']
        
        widgets = {
            'niveau': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20
            }),
            'contenu': forms.Select(attrs={
                'class': 'form-control'
            }),
            'est_obligatoire': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'ordre_dans_niveau': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }


class HistoriqueActiviteForm(forms.ModelForm):
    """Formulaire pour ajouter une entrée d'historique manuellement"""
    
    class Meta:
        model = HistoriqueActivite
        fields = [
            'enfant', 'type_activite', 'nom_activite',
            'points_gagnes', 'duree_secondes', 'reussite', 'score_activite'
        ]
        
        widgets = {
            'enfant': forms.Select(attrs={'class': 'form-control'}),
            'type_activite': forms.Select(attrs={'class': 'form-control'}),
            'nom_activite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'activité'
            }),
            'points_gagnes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'duree_secondes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'reussite': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'score_activite': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }


# ============================================
# FORMULAIRES DE RECHERCHE ET EXPORT
# ============================================

class ExportRapportForm(forms.Form):
    """Formulaire pour exporter un rapport"""
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='📅 Date de début'
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='📅 Date de fin'
    )
    
    format_export = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='📄 Format'
    )
    
    inclure_graphiques = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='📊 Inclure les graphiques'
    )
