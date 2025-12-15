from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta

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


class Badge(models.Model):
    BADGE_TYPES = [
        ('nouveau_parent', '🌟 Nouveau Parent'),
        ('premier_pas', '✍️ Premier Pas'),
        ('parent_engage', '💬 Parent Engagé'),
        ('parent_aidant', '❤️ Parent Aidant'),
        ('pilier', '🎖️ Pilier de la Communauté'),
        ('mentor', '🤝 Mentor'),
        ('famille', '👪 Famille ComAutis'),
    ]
    
    name = models.CharField(max_length=50, choices=BADGE_TYPES, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=10)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
        verbose_name = "Badge Utilisateur"
        verbose_name_plural = "Badges Utilisateurs"
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.get_name_display()}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reaction', '❤️ Réaction'),
        ('comment', '💬 Commentaire'),
        ('badge', '🎉 Badge'),
        ('mention', '📢 Mention'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"


class Activite(models.Model):
    """Enregistre chaque session de jeu/activité d'un enfant"""
    
    JEUX_CHOICES = [
        ('memory', '🧠 Memory'),
        ('compter_3', '🔢 Compter jusqu\'à 3'),
        ('compter_10', '🔢 Compter jusqu\'à 10'),
        ('couleurs', '🎨 Apprendre les Couleurs'),
        ('emotions', '😊 Reconnaître les Émotions'),
        ('memory_fruits', '🍎 Memory Fruits'),
        ('jours_semaine', '📅 Jours de la Semaine'),
        ('animaux', '🐶 Cris des Animaux'),
        ('fruits', '🍓 Apprendre les Fruits'),
        ('memory_couleurs', '🌈 Memory Couleurs'),
        ('saisons', '🍂 Les Saisons'),
        ('puzzle', '🧩 Puzzle'),
        ('labyrinthe', '🎯 Labyrinthe'),
        ('pictogrammes', '📊 Pictogrammes'),
        ('dessiner', '✏️ Dessiner'),
        ('videos', '🎥 Vidéos'),
        ('histoires', '📖 Histoires'),
    ]
    
    # Lien avec l'enfant
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='activites')
    
    # Informations sur l'activité
    jeu = models.CharField(max_length=50, choices=JEUX_CHOICES)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    duree_minutes = models.IntegerField(default=0, help_text="Durée en minutes")
    
    # Performance (optionnel)
    score = models.IntegerField(null=True, blank=True)
    reussi = models.BooleanField(default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.enfant.prenom} - {self.get_jeu_display()} - {self.date_debut.strftime('%d/%m/%Y')}"
    
    def calculer_duree(self):
        """Calcule la durée en minutes entre date_debut et date_fin"""
        if self.date_fin:
            duree = self.date_fin - self.date_debut
            self.duree_minutes = int(duree.total_seconds() / 60)
            self.save()
        return self.duree_minutes
    
    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"
        ordering = ['-date_debut']


# ========================================
# ✨ NOUVEAUX MODÈLES POUR LES ÉDUCATEURS
# ========================================

class EducateurEnfant(models.Model):
    """Relation entre un éducateur et un enfant qu'il suit"""
    educateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enfants_suivis')
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='educateurs')
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    # Notes de l'éducateur
    notes_privees = models.TextField(blank=True, null=True, help_text="Notes privées de l'éducateur")
    objectifs = models.TextField(blank=True, null=True, help_text="Objectifs fixés pour cet enfant")
    
    # Statut
    statut = models.CharField(max_length=20, default='actif', choices=[
        ('actif', 'Actif'),
        ('archive', 'Archivé'),
    ])
    
    class Meta:
        unique_together = ('educateur', 'enfant')
        verbose_name = "Éducateur-Enfant"
        verbose_name_plural = "Éducateurs-Enfants"
        ordering = ['-date_ajout']
    
    def __str__(self):
        return f"{self.educateur.username} suit {self.enfant.prenom}"


class ObservationEducateur(models.Model):
    """Observations de l'éducateur sur un enfant"""
    educateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='observations')
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='observations')
    
    date_observation = models.DateTimeField(auto_now_add=True)
    titre = models.CharField(max_length=200)
    description = models.TextField()
    
    # Type d'observation
    TYPE_CHOICES = [
        ('progres', '📈 Progrès'),
        ('difficulte', '⚠️ Difficulté'),
        ('comportement', '😊 Comportement'),
        ('reussite', '🎉 Réussite'),
        ('autre', '📝 Autre'),
    ]
    type_observation = models.CharField(max_length=20, choices=TYPE_CHOICES, default='autre')
    
    # Visible par le parent ?
    visible_parent = models.BooleanField(default=True, help_text="Le parent peut-il voir cette observation ?")
    
    class Meta:
        verbose_name = "Observation Éducateur"
        verbose_name_plural = "Observations Éducateur"
        ordering = ['-date_observation']
    
    def __str__(self):
        return f"{self.titre} - {self.enfant.prenom} ({self.date_observation.strftime('%d/%m/%Y')})"