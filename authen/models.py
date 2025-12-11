from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('parent', 'Parent'),
        ('educator', 'Éducateur'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='parent')
    phone = models.CharField(max_length=20, blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
    
    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"

class Enfant(models.Model):
    GENRE_CHOICES = [
        ('M', 'Garçon'),
        ('F', 'Fille'),
        ('A', 'Autre'),
    ]
    
    NIVEAU_AUTONOMIE_CHOICES = [
        ('faible', 'Faible autonomie'),
        ('moyen', 'Autonomie moyenne'),
        ('eleve', 'Autonomie élevée'),
    ]
    
    # Lien avec le parent
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enfants')
    
    # Informations de base
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES, default='M')
    
    # Informations spécifiques à l'autisme
    niveau_autonomie = models.CharField(max_length=20, choices=NIVEAU_AUTONOMIE_CHOICES, default='moyen')
    besoins_specifiques = models.TextField(blank=True, null=True, help_text="Sensibilités, préférences, particularités...")
    
    # Préférences
    couleur_preferee = models.CharField(max_length=50, blank=True, null=True)
    activites_preferees = models.TextField(blank=True, null=True, help_text="Jeux, activités favorites...")
    
    # Photo (optionnel)
    photo = models.ImageField(upload_to='enfants/', blank=True, null=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    def age(self):
        """Calcule l'âge de l'enfant"""
        from datetime import date
        today = date.today()
        return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
    
    class Meta:
        verbose_name = "Enfant"
        verbose_name_plural = "Enfants"
        ordering = ['-created_at']

    # Modèle Profil Educateur ********    
class ProfilEducateur(models.Model):
    """
    Profil public d'un éducateur
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_educateur')
    
    # Informations de base
    nom_complet = models.CharField(max_length=100)
    specialite = models.CharField(max_length=200, help_text="Ex: Autisme, Troubles du langage, etc.")
    photo = models.ImageField(upload_to='educateurs/', blank=True, null=True)
    
    # ✅ NOUVEAU : Relation avec les enfants suivis
    enfants_suivis = models.ManyToManyField('progression.EnfantProgression', related_name='educateurs', blank=True)
    
    # Informations professionnelles
    etablissement = models.CharField(max_length=200, blank=True)
    annees_experience = models.IntegerField(default=0)
    certifications = models.TextField(blank=True, help_text="Liste des certifications")
    
    # Bio et présentation
    bio = models.TextField(help_text="Présentation de l'éducateur")
    methodologie = models.TextField(blank=True, help_text="Approches pédagogiques utilisées")
    
    # Statistiques
    nombre_enfants = models.IntegerField(default=0, help_text="Nombre d'enfants suivis")
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Visibilité
    est_actif = models.BooleanField(default=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Profil Éducateur"
        verbose_name_plural = "Profils Éducateurs"
        ordering = ['-note_moyenne', '-nombre_enfants']
    
    def __str__(self):
        return f"{self.nom_complet} - {self.specialite}"
    
    def save(self, *args, **kwargs):
        # Mettre à jour le nombre d'enfants automatiquement
        super().save(*args, **kwargs)
        self.nombre_enfants = self.enfants_suivis.count()
        super().save(update_fields=['nombre_enfants'])


class Temoignage(models.Model):
    """
    Témoignages sur un éducateur
    """
    educateur = models.ForeignKey(ProfilEducateur, on_delete=models.CASCADE, related_name='temoignages')
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    
    note = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 à 5 étoiles
    commentaire = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Témoignage"
        ordering = ['-date']
    
    def __str__(self):
        return f"Avis de {self.parent.username} sur {self.educateur.nom_complet}"
class MessageEducateur(models.Model):
    """
    Messages entre parents et éducateurs
    """
    educateur = models.ForeignKey(ProfilEducateur, on_delete=models.CASCADE, related_name='messages_recus')
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    
    sujet = models.CharField(max_length=200)
    message = models.TextField()
    
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    
    # Réponse (optionnel)
    reponse = models.TextField(blank=True, null=True)
    date_reponse = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Message"
        ordering = ['-date_envoi']
    
    def __str__(self):
        return f"Message de {self.expediteur.username} à {self.educateur.nom_complet}"from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# ============================================
# ENFANT PROGRESSION
# ============================================

class EnfantProgression(models.Model):
    """Modèle pour suivre la progression d'un enfant"""
    nom_enfant = models.CharField(max_length=100)
    niveau_actuel = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(20)])
    score_total = models.IntegerField(default=0)
    activites_terminees = models.IntegerField(default=0)
    activites_totales = models.IntegerField(default=10)
    derniere_activite = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Enfant progression"
        verbose_name_plural = "Enfant progressions"
        ordering = ['-date_modification']
    
    def __str__(self):
        return f"{self.nom_enfant} - Niveau {self.niveau_actuel}"
    
    def pourcentage_progression(self):
        if self.activites_totales == 0:
            return 0
        return int((self.activites_terminees / self.activites_totales) * 100)
    
    def points_pour_niveau_suivant(self):
        return self.niveau_actuel * 100
    
    def score_total_requis(self):
        if self.niveau_actuel == 1:
            return 0
        return sum(i * 100 for i in range(1, self.niveau_actuel))
    
    def score_pour_niveau_actuel(self):
        return self.score_total - self.score_total_requis()
    
    def peut_monter_niveau(self):
        if self.niveau_actuel >= 20:
            return False
        score_actuel = self.score_pour_niveau_actuel()
        return score_actuel >= self.points_pour_niveau_suivant()
    
    def monter_niveau(self):
        if self.peut_monter_niveau():
            self.niveau_actuel += 1
            self.activites_totales += 5
            self.save()
            return True
        return False
    
    def terminer_activite(self, points=20):
        self.activites_terminees += 1
        self.score_total += points
        self.save()
        if self.peut_monter_niveau():
            self.monter_niveau()


# ============================================
# HISTORIQUE ACTIVITE
# ============================================

class HistoriqueActivite(models.Model):
    TYPE_ACTIVITE_CHOICES = [
        ('jeu', 'Jeu'),
        ('video', 'Vidéo'),
        ('exercice', 'Exercice'),
        ('lecture', 'Lecture'),
        ('coloriage', 'Coloriage'),
        ('autre', 'Autre'),
    ]
    
    enfant = models.ForeignKey(EnfantProgression, on_delete=models.CASCADE, related_name='historique_activites')
    type_activite = models.CharField(max_length=20, choices=TYPE_ACTIVITE_CHOICES)
    nom_activite = models.CharField(max_length=200)
    points_gagnes = models.IntegerField(default=0)
    duree_minutes = models.IntegerField(null=True, blank=True)
    date_activite = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Historique d'activité"
        verbose_name_plural = "Historiques d'activités"
        ordering = ['-date_activite']
    
    def __str__(self):
        return f"{self.enfant.nom_enfant} - {self.nom_activite}"


# ============================================
# BADGE
# ============================================

class Badge(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    icone = models.CharField(max_length=10, default='🏆')
    couleur = models.CharField(max_length=7, default='#FFD700')
    condition_type = models.CharField(max_length=50, choices=[
        ('niveau', 'Atteindre un niveau'),
        ('score', 'Atteindre un score'),
        ('activites', 'Nombre d\'activités'),
        ('jours_consecutifs', 'Jours consécutifs'),
    ], default='niveau')
    condition_valeur = models.IntegerField(default=1)
    points_bonus = models.IntegerField(default=50)
    est_actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        ordering = ['condition_valeur']
    
    def __str__(self):
        return f"{self.icone} {self.nom}"


# ============================================
# BADGE OBTENU
# ============================================

class BadgeObtenu(models.Model):
    enfant = models.ForeignKey(EnfantProgression, on_delete=models.CASCADE, related_name='badges_obtenus')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    date_obtention = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Badge obtenu"
        verbose_name_plural = "Badges obtenus"
        unique_together = ['enfant', 'badge']
        ordering = ['-date_obtention']
    
    def __str__(self):
        return f"{self.enfant.nom_enfant} - {self.badge.nom}"


# ============================================
# CATEGORIE
# ============================================

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=10, default='📁')
    couleur = models.CharField(max_length=7, default='#3498db')
    ordre_affichage = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['ordre_affichage', 'nom']
    
    def __str__(self):
        return f"{self.icone} {self.nom}"


# ============================================
# CONTENU
# ============================================

class Contenu(models.Model):
    TYPE_CONTENU_CHOICES = [
        ('jeu', 'Jeu'),
        ('video', 'Vidéo'),
        ('son', 'Audio/Son'),
        ('coloriage', 'Coloriage'),
        ('histoire', 'Histoire'),
        ('exercice', 'Exercice'),
    ]
    
    DIFFICULTE_CHOICES = [
        (1, 'Très facile'),
        (2, 'Facile'),
        (3, 'Moyen'),
        (4, 'Difficile'),
        (5, 'Très difficile'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField()
    type_contenu = models.CharField(max_length=20, choices=TYPE_CONTENU_CHOICES)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name='contenus')
    niveau_min = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(20)])
    niveau_max = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(20)])
    difficulte = models.IntegerField(choices=DIFFICULTE_CHOICES, default=2)
    duree_estimee = models.CharField(max_length=50, blank=True)
    points_recompense = models.IntegerField(default=10)
    objectif_pedagogique = models.TextField(blank=True)
    competences_travaillees = models.TextField(blank=True)
    tags = models.CharField(max_length=200, blank=True)
    fichier = models.FileField(upload_to='contenus/%Y/%m/', blank=True, null=True)
    image_preview = models.ImageField(upload_to='previews/%Y/%m/', blank=True, null=True)
    url_externe = models.URLField(blank=True)
    fichier_solution = models.FileField(upload_to='solutions/%Y/%m/', blank=True, null=True)
    est_actif = models.BooleanField(default=True)
    est_premium = models.BooleanField(default=False)
    est_valide = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Contenu éducatif"
        verbose_name_plural = "Contenus éducatifs"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_contenu_display()})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.niveau_min > self.niveau_max:
            raise ValidationError({'niveau_max': 'Le niveau maximum doit être >= au niveau minimum.'})
    
    def taux_completion(self):
        return 0


# ============================================
# EVALUATION CONTENU
# ============================================

class EvaluationContenu(models.Model):
    contenu = models.ForeignKey(Contenu, on_delete=models.CASCADE, related_name='evaluations')
    evaluateur = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    commentaire = models.TextField(blank=True)
    date_evaluation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Évaluation de contenu"
        verbose_name_plural = "Évaluations de contenus"
        unique_together = ['contenu', 'evaluateur']
        ordering = ['-date_evaluation']
    
    def __str__(self):
        return f"{self.contenu.titre} - {self.note}/5"


# ============================================
# NIVEAU CONTENU
# ============================================

class NiveauContenu(models.Model):
    contenu = models.ForeignKey(Contenu, on_delete=models.CASCADE, related_name='niveaux_associes')
    niveau = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    est_obligatoire = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Contenu de niveau"
        verbose_name_plural = "Contenus de niveaux"
        unique_together = ['contenu', 'niveau']
        ordering = ['niveau']
    
    def __str__(self):
        return f"{self.contenu.titre} - Niveau {self.niveau}"
