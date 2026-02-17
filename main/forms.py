from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.views.generic import FormView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
import re


class LoginForm(AuthenticationForm):

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "example@mail.com"
        })
    )

    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Введите пароль"
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'password')

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com'
        }),
        label="Email",
        error_messages={
            'required': 'Введите email',
            'invalid': 'Введите корректный email'
        }
    )

    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 999-99-99'
        }),
        label="Номер телефона",
        error_messages={
            'required': 'Введите номер телефона'
        }
    )

    password1 = forms.CharField(
        label="Пароль",
        min_length=3,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Придумайте пароль'
        }),
        error_messages={
            'required': 'Введите пароль',
            'min_length': 'Пароль должен быть минимум 3 символа'
        }
    )

    password2 = forms.CharField(
        label="Повторите пароль",
        min_length=3,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        }),
        error_messages={
            'required': 'Повторите пароль',
            'min_length': 'Пароль должен быть минимум 3 символа'
        }
    )

    invite_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Реферальный код (если есть)'
        }),
        label="Реферальный код"
    )

    class Meta:
        model = User
        fields = ('email', 'phone', 'password1', 'password2', 'invite_code')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")

        return password2

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = re.sub(r'[^0-9+]', '', phone)

        if not phone.startswith('+'):
            phone = '+' + phone

        digits = phone[1:]

        if not digits.isdigit() or not (10 <= len(digits) <= 15):
            raise forms.ValidationError("Введите корректный номер телефона")

        return phone

    def clean_invite_code(self):
        code = self.cleaned_data.get('invite_code', '').strip().upper()

        if code and not User.objects.filter(referral_code=code).exists():
            raise forms.ValidationError("Такой реферальный код не найден")

        return code


# class RegisterForm(UserCreationForm):
#     email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
#         'class': 'form-control',
#         'placeholder': 'Ваш email'
#     }))
#     phone = forms.CharField(required=True, widget=forms.TextInput(attrs={
#         'class': 'form-control',
#         'placeholder': '+7 (XXX) XXX-XX-XX'
#     }))
#     invite_code = forms.CharField(required=False, widget=forms.TextInput(attrs={
#         'class': 'form-control',
#         'placeholder': 'Реферальный код (если есть)'
#     }))

#     class Meta:
#         model = User
#         fields = ('email', 'phone', 'password1', 'password2', 'invite_code')

#     def clean_phone(self):
#         phone = self.cleaned_data.get('phone', '')
#         phone = re.sub(r'[^0-9+]', '', phone)
#         if not phone.startswith('+'):
#             phone = '+' + phone
#         digits = phone[1:]
#         if not digits.isdigit() or not (10 <= len(digits) <= 15):
#             raise forms.ValidationError("Неверный формат номера телефона")
#         return phone

#     def clean_invite_code(self):
#         code = self.cleaned_data.get('invite_code', '').strip().upper()
#         if code and not User.objects.filter(referral_code=code).exists():
#             raise forms.ValidationError("Такой реферальный код не найден")
#         return code


class VerifyEmailForm(forms.Form):
    code = forms.CharField(
        label="Код подтверждения",
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "123456",
            "autocomplete": "off"
        })
    )


class OrderConfirmForm(forms.Form):
    code = forms.CharField(
        label="Код подтверждения",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123456',
            'autocomplete': 'off'
        })
    )