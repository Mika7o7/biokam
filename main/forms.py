from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
import re

# Форма с исправлением: переименовали поле для ввода кода реферера, чтобы избежать конфликта с моделью
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваш email'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX',
            'id': 'phone-input',
            'data-mask': '+7 (999) 999-99-99'
        }),
        help_text="Введите номер телефона в международном формате"
    )
    invite_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Реферальный код (если есть)'
        }),
        help_text="Введите реферальный код пригласившего"
    )
    code_word = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Кодовое слово (необязательно)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2', 'code_word')  # ← Убрали 'referral_code', т.к. оно генерируется автоматически в модели

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Подставляем реферальный код из GET-параметра ?ref=... в invite_code
        if 'invite_code' in self.initial:
            self.fields['invite_code'].initial = self.initial['invite_code']

        # Bootstrap-классы для всех полей
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not phone.startswith('+'):
            phone = '+' + phone

        digits = phone[1:]
        if not digits.isdigit() or not (10 <= len(digits) <= 15):
            raise forms.ValidationError("Номер телефона должен содержать от 10 до 15 цифр и состоять только из цифр после +")

        return phone