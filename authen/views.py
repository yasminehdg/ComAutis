from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import UserProfile, Enfant
from datetime import datetime

def index(request):
    return render(request, 'authen/index.html')

def register(request):
    if request.method == "POST":
        # Récupérer les données du formulaire
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_type = request.POST.get('user_type')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        institution = request.POST.get('institution', '')
        educator_code = request.POST.get('educator_code', '')
        
        # Vérifications de base
        if password != confirm_password:
            error = "Les mots de passe ne correspondent pas"
            return render(request, 'authen/register.html', {'error': error})
        
        if User.objects.filter(username=username).exists():
            error = "Ce nom d'utilisateur existe déjà"
            return render(request, 'authen/register.html', {'error': error})
        
        if User.objects.filter(email=email).exists():
            error = "Cet email est déjà utilisé"
            return render(request, 'authen/register.html', {'error': error})
        
        # VÉRIFICATION SPÉCIALE POUR LES ÉDUCATEURS
        if user_type == 'educator':
            # Code secret pour les éducateurs (à changer en production)
            EDUCATOR_SECRET_CODE = "COMAUTISTE2024"
            
            if educator_code != EDUCATOR_SECRET_CODE:
                error = "❌ Code d'accès éducateur incorrect. Contactez l'administration."
                return render(request, 'authen/register.html', {'error': error})
            
            if not institution:
                error = "L'établissement est obligatoire pour les éducateurs"
                return render(request, 'authen/register.html', {'error': error})
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fullname
        )
        
        # Pour les éducateurs, compte INACTIF par défaut (validation admin requise)
        if user_type == 'educator':
            user.is_active = False  # Compte désactivé jusqu'à validation
            user.save()
        
        # Créer le profil utilisateur avec les infos supplémentaires
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone,
            institution=institution
        )
        
        # Redirection selon le type
        if user_type == 'educator':
            # Message de validation en attente pour éducateur
            return render(request, 'authen/educator_pending.html', {
                'username': username,
                'email': email
            })
        else:
            # Connecter automatiquement les parents
            login(request, user)
            return redirect('dashboard')
    
    return render(request, 'authen/register.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Vérifier si le compte est actif
            if not user.is_active:
                error = "⏳ Votre compte éducateur est en attente de validation. Vous recevrez un email une fois validé."
                return render(request, 'authen/login.html', {'error': error})
            
            login(request, user)
            return redirect('dashboard')
        else:
            error = "❌ Nom d'utilisateur ou mot de passe incorrect"
            return render(request, 'authen/login.html', {'error': error})
    
    return render(request, 'authen/login.html')


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def dashboard(request):
    # Récupérer le profil de l'utilisateur
    try:
        user_profile = request.user.profile
        user_type = user_profile.user_type
    except UserProfile.DoesNotExist:
        # Si pas de profil, créer un profil par défaut
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
        user_type = 'parent'
    
    # Rediriger vers le bon dashboard selon le type
    if user_type == 'educator':
        return render(request, 'authen/dashboard_educator.html', {
            'user': request.user,
            'profile': user_profile
        })
    else:  # parent
        return render(request, 'authen/dashboard_parent.html', {
            'user': request.user,
            'profile': user_profile
        })


# Nouvelle vue pour voir tous les utilisateurs (à protéger en production!)
@login_required
def users_list(request):
    # Récupérer tous les utilisateurs
    all_users = User.objects.all().order_by('-date_joined')
    
    # Compter les utilisateurs
    total_users = all_users.count()
    
    context = {
        'users': all_users,
        'total_users': total_users,
    }
    return render(request, 'authen/users_list.html', context)

@login_required
def profil_famille(request):
    # Récupérer le profil de l'utilisateur
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, user_type='parent')
    
    # Récupérer tous les enfants de l'utilisateur
    enfants = Enfant.objects.filter(parent=request.user)
    
    context = {
        'user': request.user,
        'profile': user_profile,
        'enfants': enfants,
    }
    
    return render(request, 'authen/profil_famille.html', context)


# ✨ NOUVELLE VUE : Ajouter un enfant
@login_required
def ajouter_enfant(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        date_naissance = request.POST.get('date_naissance')
        genre = request.POST.get('genre')
        niveau_autonomie = request.POST.get('niveau_autonomie')
        besoins_specifiques = request.POST.get('besoins_specifiques', '')
        couleur_preferee = request.POST.get('couleur_preferee', '')
        activites_preferees = request.POST.get('activites_preferees', '')
        
        # Créer l'enfant
        Enfant.objects.create(
            parent=request.user,
            prenom=prenom,
            nom=nom,
            date_naissance=date_naissance,
            genre=genre,
            niveau_autonomie=niveau_autonomie,
            besoins_specifiques=besoins_specifiques,
            couleur_preferee=couleur_preferee,
            activites_preferees=activites_preferees
        )
        
        return redirect('profil_famille')
    
    return render(request, 'authen/ajouter_enfant.html')


# ✨ NOUVELLE VUE : Modifier un enfant
@login_required
def modifier_enfant(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    if request.method == 'POST':
        # Mettre à jour les informations
        enfant.prenom = request.POST.get('prenom')
        enfant.nom = request.POST.get('nom')
        enfant.date_naissance = request.POST.get('date_naissance')
        enfant.genre = request.POST.get('genre')
        enfant.niveau_autonomie = request.POST.get('niveau_autonomie')
        enfant.besoins_specifiques = request.POST.get('besoins_specifiques', '')
        enfant.couleur_preferee = request.POST.get('couleur_preferee', '')
        enfant.activites_preferees = request.POST.get('activites_preferees', '')
        enfant.save()
        
        return redirect('profil_famille')
    
    context = {
        'enfant': enfant
    }
    
    return render(request, 'authen/modifier_enfant.html', context)


@login_required
def supprimer_enfant(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    if request.method == 'POST':
        enfant.delete()
        return redirect('profil_famille')
    
    context = {
        'enfant': enfant
    }
    
    return render(request, 'authen/supprimer_enfant.html', context)

@login_required
def selection_enfant(request):
    """Page de sélection de l'enfant qui veut jouer"""
    # Récupérer tous les enfants de l'utilisateur
    enfants = Enfant.objects.filter(parent=request.user)
    
    context = {
        'enfants': enfants,
        'user': request.user,
    }
    
    return render(request, 'authen/selection_enfant.html', context)


@login_required
def dashboard_enfant(request, enfant_id):
    """Dashboard personnalisé pour l'enfant"""
    # Récupérer l'enfant (vérifier qu'il appartient bien au parent connecté)
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    context = {
        'enfant': enfant,
        'user': request.user,
    }
    
    return render(request, 'authen/dashboard_enfant.html', context)

@login_required
def jeux_enfant(request, enfant_id):
    """Page de sélection des jeux pour un enfant"""
    enfant = get_object_or_404(Enfant, id=enfant_id, parent=request.user)
    
    context = {
        'enfant': enfant,
    }
    
    return render(request, 'authen/jeux_enfant.html', context)


@login_required
def users_list(request):
    # Récupérer tous les utilisateurs
    all_users = User.objects.all().order_by('-date_joined')
    
    # Compter les utilisateurs
    total_users = all_users.count()
    
    context = {
        'users': all_users,
        'total_users': total_users,
    }
    return render(request, 'authen/users_list.html', context)


# VUES POUR LES JEUX
@login_required
def liste_jeux(request):
    """Page listant tous les jeux disponibles"""
    return render(request, 'authen/jeux/liste_jeux.html')


# VUES POUR LES JEUX
@login_required
def liste_jeux(request):
    """Page listant tous les jeux disponibles"""
    return render(request, 'authen/jeux/liste_jeux.html')


@login_required
def jeu_memory(request):
    """Jeu Memory"""
    return render(request, 'authen/jeux/memory.html')

@login_required
def jeu_compter_3(request):
    """Jeu pour apprendre à compter jusqu'à 3"""
    return render(request, 'authen/jeux/compter_3.html')