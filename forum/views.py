from django.shortcuts import render, redirect, get_object_or_404
from .models import Topic, Post, Reaction
from .forms import TopicForm, PostForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from authen.badge_manager import check_and_award_badges, create_notification
from django.db.models import Count

def topic_list(request):
    # Récupérer le filtre de catégorie (salon)
    selected_category = request.GET.get('category', None)
    
    if selected_category:
        topics = Topic.objects.filter(category=selected_category).order_by('-created_at')
    else:
        topics = Topic.objects.all().order_by('-created_at')
    
    # Compter les topics par catégorie - NOUVELLE MÉTHODE
    category_counts = []
    for choice, label in Topic.CATEGORY_CHOICES:
        count = Topic.objects.filter(category=choice).count()
        category_counts.append({
            'choice': choice,
            'label': label,
            'count': count
        })
    
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.created_by = request.user
            topic.save()
            
            # Vérifier les badges
            check_and_award_badges(request.user)
            
            return redirect('forum:topic_list')
    else:
        form = TopicForm()
    
    context = {
        'topics': topics,
        'form': form,
        'selected_category': selected_category,
        'category_counts': category_counts,  # ← Liste au lieu de dict
    }
    
    return render(request, 'forum/topic_list.html', context)


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    posts = Post.objects.filter(topic=topic).order_by('created_at')

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            
            # Vérifier les badges
            check_and_award_badges(request.user)
            
            # Notifier le créateur du topic
            if request.user != topic.created_by:
                create_notification(
                    topic.created_by,
                    'comment',
                    f"💬 {request.user.username} a répondu à votre sujet : {topic.title}",
                    f'/forum/{topic.id}/'
                )
            
            return redirect('forum:topic_detail', topic_id=topic.id)
    else:
        form = PostForm()

    return render(request, 'forum/topic_detail.html', {'topic': topic, 'posts': posts, 'form': form})


@login_required
def add_reaction(request, topic_id):
    if request.method == 'POST':
        topic = Topic.objects.get(id=topic_id)
        reaction_type = request.POST.get('reaction_type')
        
        # Vérifier si l'utilisateur a déjà réagi avec ce type
        reaction, created = Reaction.objects.get_or_create(
            topic=topic,
            user=request.user,
            reaction_type=reaction_type
        )
        
        if not created:
            # Si la réaction existe déjà, la supprimer (toggle)
            reaction.delete()
            action = 'removed'
        else:
            action = 'added'
            
            # Vérifier les badges du créateur du topic
            check_and_award_badges(topic.created_by)
            
            # Créer une notification pour le créateur du topic
            if request.user != topic.created_by:
                emoji = dict(Reaction.REACTION_CHOICES).get(reaction_type, '👍')
                create_notification(
                    topic.created_by,
                    'reaction',
                    f"{emoji} {request.user.username} a réagi à votre sujet : {topic.title}",
                    f'/forum/{topic.id}/'
                )
        
        # Compter toutes les réactions par type
        reaction_counts = {}
        for choice, emoji in Reaction.REACTION_CHOICES:
            count = topic.reactions.filter(reaction_type=choice).count()
            reaction_counts[choice] = count
        
        return JsonResponse({
            'action': action,
            'reaction_counts': reaction_counts
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)