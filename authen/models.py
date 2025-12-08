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
        