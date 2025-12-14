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
    
    # ✅ NOUVEAU : Champ pour la photo de profil
    photo_profil = models.ImageField(upload_to='photos_profil/', blank=True, null=True)
    
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
    
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='activites')
    jeu = models.CharField(max_length=50, choices=JEUX_CHOICES)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    duree_minutes = models.IntegerField(default=0, help_text="Durée en minutes")
    score = models.IntegerField(null=True, blank=True)
    reussi = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.enfant.prenom} - {self.get_jeu_display()} - {self.date_debut.strftime('%d/%m/%Y')}"
    
    def calculer_duree(self):
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
# MODÈLE PRÉFÉRENCES UTILISATEUR
# ========================================

class UserPreferences(models.Model):
    """Modèle pour stocker les préférences utilisateur"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notifications
    notifications_email = models.BooleanField(default=True)
    rappels_routine = models.BooleanField(default=True)
    alertes_forum = models.BooleanField(default=False)
    newsletter = models.BooleanField(default=True)
    
    # Affichage
    THEME_CHOICES = [
        ('clair', 'Mode clair'),
        ('sombre', 'Mode sombre'),
        ('auto', 'Automatique'),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='clair')
    
    TAILLE_CHOICES = [
        ('petite', 'Petite'),
        ('normale', 'Normale'),
        ('grande', 'Grande'),
        ('tres_grande', 'Très grande'),
    ]
    taille_police = models.CharField(max_length=15, choices=TAILLE_CHOICES, default='normale')
    
    LANGUE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
    ]
    langue = models.CharField(max_length=5, choices=LANGUE_CHOICES, default='fr')
    contraste_eleve = models.BooleanField(default=False)
    
    # Sons
    sons_jeux = models.BooleanField(default=True)
    musique_fond = models.BooleanField(default=False)
    
    VOLUME_CHOICES = [
        ('silencieux', 'Silencieux'),
        ('faible', 'Faible'),
        ('moyen', 'Moyen'),
        ('fort', 'Fort'),
    ]
    volume = models.CharField(max_length=15, choices=VOLUME_CHOICES, default='moyen')
    lecture_vocale = models.BooleanField(default=False)
    
    # Confidentialité
    VISIBILITE_CHOICES = [
        ('tous', 'Tous les membres'),
        ('amis', 'Amis uniquement'),
        ('prive', 'Privé'),
    ]
    visibilite_profil = models.CharField(max_length=10, choices=VISIBILITE_CHOICES, default='tous')
    partage_donnees = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Préférences de {self.user.username}"
    
    class Meta:
        verbose_name = "Préférence utilisateur"
        verbose_name_plural = "Préférences utilisateur"