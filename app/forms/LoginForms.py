from django import forms
from django.contrib.auth import user_login_failed
from django.utils.translation import gettext_lazy as _
from django_otp import match_token
from django_otp.forms import OTPAuthenticationForm


class MyAuthenticationForm(OTPAuthenticationForm):

    otp_token = forms.RegexField(
        regex=r'^\d{6}$',
        widget=forms.TextInput(),
        error_messages={
            'invalid': 'Enter a valid otp. Must be 6 digits.'
        }
    )

    error_messages = {
        'invalid_login':
            _("Invalid Credentials.<br>"
              "Please enter a correct username and password.<br>")
        ,
        'inactive': _("This account is inactive."),
    }

    def get_user(self):
        user = self.user_cache

        return user

    def verify(self):
        if self.request.user.is_verified():
            return True

        if not self.request.user.is_authenticated:
            user_login_failed.send(
                sender=self.request.user,
                request=self.request,
                credentials={
                    'username': self.cleaned_data['username']
                }
            )

        return False

    def _verify_token(self, user, token, device=None):
        if device is not None:
            device = device if device.verify_token(token) else None
        else:
            device = match_token(user, token)

        if device is None:
            self.verify()

            raise forms.ValidationError(_('Invalid token. Please make sure you have entered it correctly.'), code='invalid')

        return device

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        self.fields.pop('otp_device')
        self.fields.pop('otp_challenge')
