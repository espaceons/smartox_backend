from django import forms
from django.forms import inlineformset_factory
from .models import Prescription, PrescriptionItem

# Liste des compartiments IoT pour la boîte à médicaments
COMPARTMENT_CHOICES = [
    (1, "Compartiment IoT 1"),
    (2, "Compartiment IoT 2"),
    (3, "Compartiment IoT 3"),
    (4, "Compartiment IoT 4"),
    (5, "Compartiment IoT 5"),
    (6, "Compartiment IoT 6"),
]

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Consignes ou instructions particulières pour le patient...'
            })
        }

class PrescriptionItemForm(forms.ModelForm):
    compartment_number = forms.TypedChoiceField(
        choices=COMPARTMENT_CHOICES,
        coerce=int,
        initial=1,
        label="Compartiment IoT",
        widget=forms.Select(attrs={
            'class': 'form-select border-primary fw-bold'
        }),
        help_text="Sélectionnez le casier physique dans lequel placer ce médicament."
    )

    class Meta:
        model = PrescriptionItem
        fields = [
            'medication_name',
            'dosage',
            'start_date',
            'end_date',
            'intake_time_1',
            'intake_time_2',
            'intake_time_3',
            'compartment_number',
            'item_notes',
        ]
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Paracétamol'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1000mg, 1 comprimé'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'intake_time_1': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'intake_time_2': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'intake_time_3': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'item_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Consignes spécifiques...'}),
        }

# Création du FormSet lié
PrescriptionItemFormSet = inlineformset_factory(
    Prescription,
    PrescriptionItem,
    form=PrescriptionItemForm,
    extra=1,
    can_delete=True
)