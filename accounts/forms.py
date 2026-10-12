from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import PatientProfile

User = get_user_model()


class CustomLoginForm(AuthenticationForm):
    """
    Formulaire de connexion personnalisé avec classes Bootstrap
    """
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur",
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )


class CustomUserCreationForm(UserCreationForm):
    """
    Formulaire d'inscription incluant le rôle, le prénom, le nom, l'email et le téléphone
    """
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        label="Prénom",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre prénom'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        label="Nom",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'})
    )
    email = forms.EmailField(
        required=True, 
        label="Adresse Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@domaine.com'})
    )
    role = forms.ChoiceField(
        choices=User.Role.choices,
        required=True,
        label="Type de compte",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+216 ...'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Styles Bootstrap pour les champs générés automatiquement par UserCreationForm
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': "Nom d'utilisateur"})
        self.fields['username'].help_text = None  # Masque le texte d'aide par défaut de Django

        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mot de passe'})
            self.fields['password1'].help_text = None

        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmation du mot de passe'})


class CustomUserChangeForm(UserChangeForm):
    """
    Formulaire de modification du profil utilisateur
    """
    password = None  # Masque la gestion directe du mot de passe dans l'édition classique

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }