from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class MinLength3Validator:
    def validate(self, password, user=None):
        if len(password) < 3:
            raise ValidationError(
                _("Пароль должен содержать минимум 3 символа"),
                code='password_too_short',
            )

    def get_help_text(self):
        return _("Пароль должен содержать минимум 3 символа")
