from django import forms
from django.forms import inlineformset_factory
from .models import Prescription, PrescriptionItem

COMPARTMENT_CHOICES = [(i, f"Compartiment IoT {i}") for i in range(1, 7)]

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class PrescriptionItemForm(forms.ModelForm):
    compartment_1 = forms.TypedChoiceField(
        choices=COMPARTMENT_CHOICES, coerce=int, initial=1, required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    compartment_2 = forms.TypedChoiceField(
        choices=COMPARTMENT_CHOICES, coerce=int, initial=2, required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    compartment_3 = forms.TypedChoiceField(
        choices=COMPARTMENT_CHOICES, coerce=int, initial=3, required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    class Meta:
        model = PrescriptionItem
        fields = [
            'medication_name',
            'dosage',
            'start_date',
            'end_date',
            'intake_time_1', 'compartment_1',
            'intake_time_2', 'compartment_2',
            'intake_time_3', 'compartment_3',
            'item_notes',
        ]
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Médicament 01'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1 comprimé'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'intake_time_1': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'intake_time_2': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'intake_time_3': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'item_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

PrescriptionItemFormSet = inlineformset_factory(
    Prescription, PrescriptionItem, form=PrescriptionItemForm, extra=1, can_delete=True
)