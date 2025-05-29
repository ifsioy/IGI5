from django import forms
from .models import ClientProfile, CompanyHistoryItem
from django.core.exceptions import ValidationError

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ['patronymic', 'address', 'phone_number', 'birth_date']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.startswith('+375'):
            raise ValidationError('Номер телефона должен начинаться с +375.')
        return phone_number

    def clean_birth_date(self):
        from datetime import date
        birth_date = self.cleaned_data.get('birth_date')
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise ValidationError('Возраст должен быть не менее 18 лет.')
        return birth_date

class CompanyHistoryItemForm(forms.ModelForm):
    class Meta:
        model = CompanyHistoryItem
        fields = ['year', 'event_description']
        widgets = {
            'event_description': forms.Textarea(attrs={'rows': 3}),
        }