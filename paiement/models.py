# ========================================
# FICHIER: paiement/models.py
# MODIFIÉ - Garde votre système existant + ajoute jeux premium
# ========================================

from django.db import models
from django.contrib.auth.models import User

class Level(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.price}€"

    class Meta:
        verbose_name = "Niveau d'abonnement"
        verbose_name_plural = "Niveaux d'abonnement"


class Subscription(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    simulated_payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.parent.username} - {self.level.name} - {'Actif' if self.active else 'Inactif'}"

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-start_date']


# ========================================
# ✨ NOUVEAUX MODÈLES POUR JEUX PREMIUM
# ========================================

class JeuPremium(models.Model):
    """Définit quels jeux sont premium (payants)"""
    
    JEUX_DISPONIBLES = [
        ('memory', '🧠 Memory'),
        ('compter_10', '🔢 Compter jusqu\'à 10'),
        ('puzzle', '🧩 Puzzle'),
        ('labyrinthe', '🌀 Labyrinthe'),
        ('saisons', '🌻 Les Saisons'),
    ]
    
    jeu_code = models.CharField(
        max_length=50, 
        choices=JEUX_DISPONIBLES, 
        unique=True,
        help_text="Code unique du jeu"
    )
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(max_digits=6, decimal_places=2, default=4.99)
    icone = models.CharField(max_length=10, default='🎮')
    actif = models.BooleanField(default=True, help_text="Jeu disponible à la vente")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nom} - {self.prix}€"
    
    class Meta:
        verbose_name = "Jeu Premium"
        verbose_name_plural = "Jeux Premium"
        ordering = ['nom']


class PaiementJeu(models.Model):
    """Enregistre chaque achat de jeu premium"""
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('reussi', 'Réussi'),
        ('echoue', 'Échoué'),
    ]
    
    # Qui a payé ?
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paiements_jeux')
    
    # Pour quel jeu ?
    jeu_premium = models.ForeignKey(JeuPremium, on_delete=models.CASCADE)
    
    # Informations du paiement
    montant = models.DecimalField(max_digits=6, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    
    # Informations carte (4 derniers chiffres seulement)
    numero_carte_masque = models.CharField(max_length=19, blank=True, help_text="Ex: **** **** **** 1234")
    nom_carte = models.CharField(max_length=100, blank=True)
    
    # Transaction ID unique
    transaction_id = models.CharField(max_length=100, unique=True)
    
    # Message d'erreur
    message_erreur = models.TextField(blank=True, null=True)
    
    # Dates
    date_paiement = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.parent.username} - {self.jeu_premium.nom} - {self.statut}"
    
    class Meta:
        verbose_name = "Paiement Jeu"
        verbose_name_plural = "Paiements Jeux"
        ordering = ['-date_paiement']


class AccesJeu(models.Model):
    """Donne l'accès à un jeu premium après paiement réussi"""
    
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jeux_debloques')
    jeu_premium = models.ForeignKey(JeuPremium, on_delete=models.CASCADE)
    paiement = models.ForeignKey(PaiementJeu, on_delete=models.CASCADE)
    
    date_achat = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('parent', 'jeu_premium')
        verbose_name = "Accès Jeu Premium"
        verbose_name_plural = "Accès Jeux Premium"
        ordering = ['-date_achat']
    
    def __str__(self):
        return f"{self.parent.username} - {self.jeu_premium.nom}"