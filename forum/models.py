from django.db import models
from django.contrib.auth.models import User
import random

ICON_CHOICES = ['book', 'love', 'chat', 'star', 'autumn', 'pencil']

class Topic(models.Model):
    CATEGORY_CHOICES = [
        ('ecole', '🏫 École et Scolarité'),
        ('alimentation', '🍽️ Alimentation et Repas'),
        ('sommeil', '😴 Sommeil et Routines'),
        ('jeux', '🎮 Jeux et Activités'),
        ('sante', '💊 Santé et Thérapies'),
        ('entraide', '🤝 Entraide et Soutien'),
        ('libre', '💬 Discussions Libres'),
    ]
    
    title = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    icon = models.CharField(max_length=20, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='libre')

    def save(self, *args, **kwargs):
        if not self.icon:
            self.icon = random.choice(ICON_CHOICES)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.created_by} - {self.content[:30]}'


class Reaction(models.Model):
    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('support', '💪'),
        ('celebrate', '🎉'),
    ]
    
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('topic', 'user', 'reaction_type')
        verbose_name = "Réaction"
        verbose_name_plural = "Réactions"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()} sur {self.topic.title}"