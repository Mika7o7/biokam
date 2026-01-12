from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    referral_code = forms.CharField(
        max_length=10,
        required=False,
        label="Реферальный код (если есть)",
        help_text="Введите код друга, чтобы получить бонус при первой покупке"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'referral_code')

    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if code:
            referrer = User.objects.filter(referral_code__iexact=code).first()
            if not referrer:
                raise forms.ValidationError("Такой реферальный код не существует")
            self.cleaned_data['referrer'] = referrer  # Сохраняем объект для save
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        referrer = self.cleaned_data.get('referrer')
        if referrer:
            user.referrer = referrer
        if commit:
            user.save()
        return user