from django import forms
from django.core.exceptions import ValidationError
from app.models import KnownAccount
from app.views.known_accounts import KnownAccountHelpers


class KnownAccountsForm(forms.ModelForm):

    account_number = forms.RegexField(
        regex=r'^\d{16}$',
        widget=forms.TextInput(),
        error_messages={
            'invalid': 'Enter a valid account number. Must be 16 digits.'
        }
    )

    class Meta:
        model = KnownAccount
        exclude = ('account', 'user')
        labels = {
            'account_number': "Account Number"
        }

    def clean_account_number(self):
        account_number = self.cleaned_data['account_number']

        if KnownAccountHelpers.get_account_from_number(account_number):
            return account_number

        raise ValidationError('Account Number not valid')

