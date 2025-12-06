from django.shortcuts import render, redirect, get_object_or_404
from .models import Topic, Post
from .forms import TopicForm, PostForm

def topic_list(request):
    topics = Topic.objects.all().order_by('-created_at')  # derniers topics en premier
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.created_by = request.user
            topic.save()  # l'icône sera assignée automatiquement ici
            return redirect('forum:topic_list')
    else:
        form = TopicForm()
    return render(request, 'forum/topic_list.html', {'topics': topics, 'form': form})

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
            return redirect('forum:topic_detail', topic_id=topic.id)
    else:
        form = PostForm()

    return render(request, 'forum/topic_detail.html', {'topic': topic, 'posts': posts, 'form': form})
