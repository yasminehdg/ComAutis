from django import forms
from .models import Topic, Post

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Titre du sujet...',
                'class': 'form-input'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'title': 'Titre',
            'category': 'Salon de discussion'
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': 'Votre message...',
                'rows': 4,
                'class': 'form-textarea'
            })
        }
        labels = {
            'content': 'Message'
        }