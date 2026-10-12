
from django import forms
from accounts.models import PatientProfile
from django.contrib.auth import get_user_model
from .models import PatientCaregiver

User = get_user_model()

class PatientProfileForm(forms.ModelForm):
    """
    Formulaire pour associer un médecin, un proche et préciser la date de naissance
    """
    class Meta:
        model = PatientProfile
        fields = ('doctor', 'relative', 'date_of_birth')
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'relative': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        


class LinkDoctorForm(forms.Form):
    doctor_code = forms.CharField(
        label="Code du Médecin",
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le code (ex: DOC-A1B2)',
            'required': True
        })
    )

    def clean_doctor_code(self):
        code = self.cleaned_data['doctor_code'].strip().upper()
        if not code.startswith("DOC-"):
            raise forms.ValidationError("Le code médecin doit commencer par 'DOC-'.")
        return code


class LinkPatientForm(forms.Form):
    patient_identifier = forms.CharField(
        label="Nom d'utilisateur du Patient",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le nom d\'utilisateur (ex: mohamed_ben)',
            'required': True
        })
    )
    
    
# dashboards/forms.py
from django import forms

class LinkPatientToRelativeForm(forms.Form):
    patient_identifier = forms.CharField(
        label="Identifiant du patient (Username ou Email)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: samir ou patient@email.com'
        })
    )

class LinkRelativeToPatientForm(forms.Form):
    relative_identifier = forms.CharField(
        label="Identifiant du proche (Username ou Email)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: parent@gmail.com'
        })
    )
    

# ajouter un proche soit via son adresse email, soit via son numéro de téléphone ou nom d'utilisateur.

class AddCaregiverForm(forms.Form):
    email = forms.EmailField(
        label="Adresse Email du proche",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
    )
    relationship = forms.CharField(
        label="Lien de parenté / Relation",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Fils, Fille, Voisin...'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            caregiver_user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Aucun utilisateur trouvé avec cette adresse email.")
        return email