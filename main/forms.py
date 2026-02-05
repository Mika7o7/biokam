from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.views.generic import FormView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
import re


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ваш email'
    }))
    phone = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+7 (XXX) XXX-XX-XX'
    }))
    invite_code = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Реферальный код (если есть)'
    }))

    class Meta:
        model = User
        fields = ('email', 'phone', 'password1', 'password2', 'invite_code')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = re.sub(r'[^0-9+]', '', phone)
        if not phone.startswith('+'):
            phone = '+' + phone
        digits = phone[1:]
        if not digits.isdigit() or not (10 <= len(digits) <= 15):
            raise forms.ValidationError("Неверный формат номера телефона")
        return phone

    def clean_invite_code(self):
        code = self.cleaned_data.get('invite_code', '').strip().upper()
        if code and not User.objects.filter(referral_code=code).exists():
            raise forms.ValidationError("Такой реферальный код не найден")
        return code


class VerifyEmailForm(forms.Form):
    code = forms.CharField(max_length=6, label='Код подтверждения')

# class VerifyEmailView(FormView):
#     template_name = 'registration/verify_email.html'
#     form_class = VerifyEmailForm
#     success_url = reverse_lazy('login')

#     def form_valid(self, form):
#         code = form.cleaned_data['code']
#         user = User.objects.filter(email_verification_code=code, is_active=False).first()
#         if user:
#             user.is_active = True
#             user.is_email_verified = True
#             user.email_verification_code = ''
#             user.save()
#             messages.success(self.request, 'Email подтверждён! Теперь вы можете войти.')
#             return super().form_valid(form)
#         else:
#             form.add_error('code', 'Неверный код')
#             return self.form_invalid(form)


class VerifyCodeForm(forms.Form):
    code = forms.CharField(
        label="Введите код",
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "123456",
            "autocomplete": "off"
        })
    )