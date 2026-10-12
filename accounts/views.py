from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import CustomLoginForm, CustomUserCreationForm


def redirect_by_role(user):
    """
    Redirige l'utilisateur connecté vers le dashboard correspondant à son rôle.
    """
    role = getattr(user, 'role', None)

    if role == 'DOCTOR':
        return redirect('dashboards:doctor-dashboard')
    elif role == 'RELATIVE':
        return redirect('dashboards:relative-dashboard')
    
    # Redirection par défaut (admin ou rôle non spécifié)
    return redirect('dashboards:main-dashboard')


def user_login(request):
    """
    Vue de connexion avec redirection selon le rôle de l'utilisateur.
    """
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect_by_role(user)
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """
    Déconnexion de l'utilisateur.
    """
    logout(request)
    return redirect('accounts:login')


def register_view(request):
    """
    Vue d'inscription avec connexion et redirection selon le rôle.
    """
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Connexion automatique après inscription
            login(request, user)
            messages.success(
                request, 
                f"Bienvenue {user.first_name or user.username} ! Votre compte a été créé avec succès."
            )
            return redirect_by_role(user)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})