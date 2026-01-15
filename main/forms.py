from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ваш email'})
    )

    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX',
            'id': 'phone-input'
        }),
        help_text="Введите номер телефона в международном формате"
    )

    referral_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.HiddenInput(),  # скрытое поле для автоматической подстановки
    )

    code_word = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Кодовое слово (необязательно)'
        }),
        help_text="Если у вас есть кодовое слово от пригласившего — введите его"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2', 'referral_code', 'code_word')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы bootstrap для всех полей
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class') is None:
                field.widget.attrs['class'] = 'form-control'

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Простая валидация номера (можно улучшить)
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not phone.startswith('+'):
            phone = '+' + phone
        if len(phone) < 10:
            raise forms.ValidationError("Номер телефона слишком короткий")
        return phone