from django.db import models
from django.contrib.auth.models import User

class EnfantProgression(models.Model):
    nom_enfant = models.CharField(max_length=100)
    niveau = models.IntegerField(default=1)
    score = models.IntegerField(default=0)
    activites_terminees = models.IntegerField(default=0)
    activites_totales = models.IntegerField(default=10)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Enfant progression"
        verbose_name_plural = "Enfant progressions"
    
    def __str__(self):
        return f"{self.nom_enfant} - Niveau {self.niveau}"
    
    def pourcentage_progression(self):
        """Calcule le pourcentage de progression dans le niveau actuel"""
        if self.activites_totales == 0:
            return 0
        return int((self.activites_terminees / self.activites_totales) * 100)
    
    def points_pour_niveau_suivant(self):
        """Calcule combien de points sont nécessaires pour passer au niveau suivant"""
        # Niveau 1->2: 100pts, 2->3: 200pts, 3->4: 300pts, etc.
        return self.niveau * 100
    
    def score_total_requis(self):
        """Score total nécessaire pour atteindre le niveau actuel"""
        # Somme: 0 + 100 + 200 + 300 + ... + (niveau-1)*100
        if self.niveau == 1:
            return 0
        return sum(i * 100 for i in range(1, self.niveau))
    
    def score_pour_niveau_actuel(self):
        """Score accumulé dans le niveau actuel"""
        return self.score - self.score_total_requis()
    
    def peut_monter_niveau(self):
        """Vérifie si l'enfant peut passer au niveau supérieur"""
        if self.niveau >= 20:  # Maximum 20 niveaux
            return False
        score_actuel = self.score_pour_niveau_actuel()
        return score_actuel >= self.points_pour_niveau_suivant()
    
    def monter_niveau(self):
        """Fait monter l'enfant d'un niveau"""
        if self.peut_monter_niveau():
            self.niveau += 1
            self.activites_totales += 5  # Plus d'activités par niveau
            self.save()
            return True
        return False
    
    def terminer_activite(self, points=20):
        """Marque une activité comme terminée et ajoute des points"""
        self.activites_terminees += 1
        self.score += points
        self.save()
        
        # Vérifier si l'enfant peut monter de niveau
        if self.peut_monter_niveau():
            self.monter_niveau()
    
    def message_motivation(self):
        """Retourne un message de motivation selon la progression"""
        pourcentage = self.pourcentage_progression()
        
        if pourcentage == 100:
            return "🎉 Incroyable ! Tu as tout réussi !"
        elif pourcentage >= 80:
            return "⭐ Super travail ! Continue comme ça !"
        elif pourcentage >= 60:
            return "💪 Tu es sur la bonne voie !"
        elif pourcentage >= 40:
            return "🌟 Bravo, tu progresses bien !"
        elif pourcentage >= 20:
            return "🚀 C'est parti ! Continue !"
        else:
            return "✨ Bienvenue ! Commence ton aventure !"
        
# ============================================
# NOUVEAUX MODÈLES - PARTIE 1 (Historique & Badges)
# ============================================

class HistoriqueActivite(models.Model):
    """Historique de toutes les activités effectuées par un enfant"""
    enfant = models.ForeignKey(
        EnfantProgression, 
        on_delete=models.CASCADE, 
        related_name='historique'
    )
    type_activite = models.CharField(
        max_length=50,
        choices=[
            ('jeu', 'Jeu'),
            ('video', 'Vidéo'),
            ('son', 'Son/Audio'),
            ('coloriage', 'Coloriage'),
            ('questionnaire', 'Questionnaire'),
        ]
    )
    nom_activite = models.CharField(max_length=200)
    points_gagnes = models.IntegerField(default=0)
    duree_secondes = models.IntegerField(null=True, blank=True, help_text="Durée de l'activité en secondes")
    reussite = models.BooleanField(default=True, help_text="L'activité a-t-elle été réussie ?")
    score_activite = models.IntegerField(null=True, blank=True, help_text="Score obtenu dans l'activité (si applicable)")
    date_activite = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_activite']
        verbose_name = "Historique d'activité"
        verbose_name_plural = "Historiques d'activités"
    
    def __str__(self):
        return f"{self.enfant.nom_enfant} - {self.nom_activite} ({self.date_activite.strftime('%d/%m/%Y')})"
    
    def duree_minutes(self):
        """Retourne la durée en minutes"""
        if self.duree_secondes:
            return round(self.duree_secondes / 60, 1)
        return 0


class Badge(models.Model):
    """Badges que les enfants peuvent obtenir"""
    nom = models.CharField(max_length=100)
    description = models.TextField()
    icone = models.CharField(max_length=50, help_text="Emoji ou nom d'icône")
    
    CONDITION_CHOICES = [
        ('niveau', 'Atteindre un niveau'),
        ('score', 'Atteindre un score total'),
        ('activites', 'Nombre d\'activités terminées'),
        ('jours_consecutifs', 'Jours d\'activité consécutifs'),
        ('type_activite', 'Nombre d\'activités d\'un type spécifique'),
    ]
    condition_type = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    condition_valeur = models.IntegerField(help_text="Valeur à atteindre pour obtenir le badge")
    condition_details = models.CharField(max_length=100, blank=True, help_text="Détails supplémentaires (ex: type d'activité)")
    
    couleur_fond = models.CharField(max_length=7, default='#3498db', help_text="Code couleur hexadécimal")
    ordre_affichage = models.IntegerField(default=0, help_text="Ordre d'affichage des badges")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    est_actif = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['ordre_affichage', 'nom']
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
    
    def __str__(self):
        return f"{self.icone} {self.nom}"


class BadgeObtenu(models.Model):
    """Badges obtenus par les enfants"""
    enfant = models.ForeignKey(
        EnfantProgression, 
        on_delete=models.CASCADE, 
        related_name='badges'
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    date_obtention = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['enfant', 'badge']
        ordering = ['-date_obtention']
        verbose_name = "Badge obtenu"
        verbose_name_plural = "Badges obtenus"
    
    def __str__(self):
        return f"{self.enfant.nom_enfant} - {self.badge.nom}"


# ============================================
# NOUVEAUX MODÈLES - PARTIE 3 (Gestion du Contenu)
# ============================================

class Categorie(models.Model):
    """Catégories pour organiser les contenus éducatifs"""
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=50, blank=True, help_text="Emoji ou nom d'icône")
    couleur = models.CharField(max_length=7, default='#3498db', help_text="Code couleur hexadécimal")
    ordre_affichage = models.IntegerField(default=0)
    est_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['ordre_affichage', 'nom']
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
    
    def __str__(self):
        return f"{self.icone} {self.nom}" if self.icone else self.nom
    
    def nombre_contenus(self):
        """Retourne le nombre de contenus actifs dans cette catégorie"""
        return self.contenus.filter(est_actif=True).count()


class Contenu(models.Model):
    """Contenus éducatifs (jeux, vidéos, sons, coloriages)"""
    
    TYPE_CHOICES = [
        ('jeu', 'Jeu Interactif'),
        ('video', 'Vidéo'),
        ('son', 'Son/Audio'),
        ('coloriage', 'Coloriage'),
        ('histoire', 'Histoire'),
        ('exercice', 'Exercice'),
    ]
    
    DIFFICULTE_CHOICES = [
        (1, '⭐ Très facile'),
        (2, '⭐⭐ Facile'),
        (3, '⭐⭐⭐ Moyen'),
        (4, '⭐⭐⭐⭐ Difficile'),
        (5, '⭐⭐⭐⭐⭐ Très difficile'),
    ]
    
    # Informations de base
    titre = models.CharField(max_length=200)
    description = models.TextField(help_text="Description détaillée du contenu")
    type_contenu = models.CharField(max_length=20, choices=TYPE_CHOICES)
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='contenus'
    )
    
    # Niveaux et difficulté
    niveau_min = models.IntegerField(
        default=1, 
        help_text="Niveau minimum requis pour accéder à ce contenu"
    )
    niveau_max = models.IntegerField(
        default=20, 
        help_text="Niveau maximum pour lequel ce contenu est pertinent"
    )
    difficulte = models.IntegerField(
        choices=DIFFICULTE_CHOICES,
        default=1,
        help_text="Niveau de difficulté du contenu"
    )
    
    # Métadonnées pédagogiques
    duree_estimee = models.IntegerField(
        default=5,
        help_text="Durée estimée en minutes"
    )
    points_recompense = models.IntegerField(
        default=20,
        help_text="Points accordés pour la réussite"
    )
    objectif_pedagogique = models.TextField(
        blank=True,
        help_text="Objectif pédagogique du contenu"
    )
    competences_travaillees = models.CharField(
        max_length=200,
        blank=True,
        help_text="Compétences travaillées (séparées par des virgules)"
    )
    
    # Fichiers et ressources
    fichier = models.FileField(
        upload_to='contenus/%Y/%m/',
        null=True,
        blank=True,
        help_text="Fichier du contenu (image, audio, vidéo, PDF...)"
    )
    image_preview = models.ImageField(
        upload_to='previews/%Y/%m/',
        null=True,
        blank=True,
        help_text="Image de prévisualisation"
    )
    url_externe = models.URLField(
        blank=True,
        help_text="URL externe si le contenu est hébergé ailleurs"
    )
    fichier_solution = models.FileField(
        upload_to='solutions/%Y/%m/',
        null=True,
        blank=True,
        help_text="Fichier de solution ou correction (pour les éducateurs)"
    )
    
    # Métadonnées système
    cree_par = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='contenus_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contenus_modifies'
    )
    
    # Statut et visibilité
    est_actif = models.BooleanField(
        default=True,
        help_text="Le contenu est-il visible et accessible ?"
    )
    est_premium = models.BooleanField(
        default=False,
        help_text="Réservé aux comptes premium ?"
    )
    est_valide = models.BooleanField(
        default=False,
        help_text="Validé par un administrateur ?"
    )
    
    # Statistiques
    nombre_vues = models.IntegerField(default=0)
    nombre_completions = models.IntegerField(default=0)
    note_moyenne = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        help_text="Note moyenne sur 5"
    )
    
    # Tags pour recherche
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text="Tags séparés par des virgules pour faciliter la recherche"
    )
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Contenu éducatif"
        verbose_name_plural = "Contenus éducatifs"
        indexes = [
            models.Index(fields=['type_contenu', 'est_actif']),
            models.Index(fields=['niveau_min', 'niveau_max']),
            models.Index(fields=['categorie', 'est_actif']),
        ]
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_contenu_display()})"
    
    def est_accessible_pour_niveau(self, niveau):
        """Vérifie si un enfant d'un certain niveau peut accéder à ce contenu"""
        return self.niveau_min <= niveau <= self.niveau_max
    
    def get_difficulte_display_stars(self):
        """Retourne la difficulté sous forme d'étoiles"""
        return "⭐" * self.difficulte
    
    def incrementer_vues(self):
        """Incrémente le nombre de vues"""
        self.nombre_vues += 1
        self.save(update_fields=['nombre_vues'])
    
    def incrementer_completions(self):
        """Incrémente le nombre de complétions"""
        self.nombre_completions += 1
        self.save(update_fields=['nombre_completions'])
    
    def taux_completion(self):
        """Calcule le taux de complétion (complétions / vues)"""
        if self.nombre_vues == 0:
            return 0
        return round((self.nombre_completions / self.nombre_vues) * 100, 1)


class EvaluationContenu(models.Model):
    """Évaluations/notes données aux contenus par les éducateurs ou parents"""
    contenu = models.ForeignKey(
        Contenu,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    note = models.IntegerField(
        choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)],
        help_text="Note de 1 à 5 étoiles"
    )
    commentaire = models.TextField(blank=True)
    date_evaluation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['contenu', 'utilisateur']
        ordering = ['-date_evaluation']
        verbose_name = "Évaluation de contenu"
        verbose_name_plural = "Évaluations de contenus"
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.contenu.titre} ({self.note}/5)"


class NiveauContenu(models.Model):
    """Association entre un niveau et les contenus recommandés"""
    niveau = models.IntegerField()
    contenu = models.ForeignKey(
        Contenu,
        on_delete=models.CASCADE,
        related_name='niveaux_assignes'
    )
    est_obligatoire = models.BooleanField(
        default=False,
        help_text="Ce contenu est-il obligatoire pour ce niveau ?"
    )
    ordre_dans_niveau = models.IntegerField(
        default=0,
        help_text="Ordre de présentation dans le niveau"
    )
    
    class Meta:
        unique_together = ['niveau', 'contenu']
        ordering = ['niveau', 'ordre_dans_niveau']
        verbose_name = "Contenu de niveau"
        verbose_name_plural = "Contenus de niveaux"
    
    def __str__(self):
        return f"Niveau {self.niveau} - {self.contenu.titre}"
