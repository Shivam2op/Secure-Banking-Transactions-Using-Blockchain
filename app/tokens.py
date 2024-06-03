from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
from django_otp.plugins.otp_totp.models import TOTPDevice


class OTPActivationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        device, created = TOTPDevice.objects.get_or_create(user=user, name='Phone')

        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(device.confirmed) + six.text_type(user.is_active)
        )


otp_token_generator = OTPActivationTokenGenerator()


class PIITokenGenerator(PasswordResetTokenGenerator):

    def __init__(self, target_pii, *args, **kwargs):
        self.target_pii = target_pii

        super().__init__(*args, **kwargs)

    def _make_hash_value(self, user, timestamp):
        target_pii = self.target_pii

        return (
                six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.has_perm('read_pii', target_pii)) + six.text_type(user.is_admin()) + six.text_type(user.last_login)
        )
