from django import forms
from django.core.exceptions import ValidationError
from app.models import MerchantPaymentAccount, MyUser
from app.views.known_accounts import KnownAccountHelpers


class PaymentAccountsForm(forms.ModelForm):

    account_number = forms.RegexField(
        regex=r'^\d{16}$',
        widget=forms.TextInput(),
        error_messages={
            'invalid': 'Enter a valid account number. Must be 16 digits.'
        }
    )

    class Meta:
        model = MerchantPaymentAccount
        exclude = ('account', 'merchant_user')
        labels = {
            'account_number': "Account Number"
        }

    def clean_account_number(self):
        account_number = self.cleaned_data['account_number']

        if KnownAccountHelpers.get_account_from_number(account_number):
            return account_number

        raise ValidationError('Account Number not valid')



class RemovePaymentAccountForm(forms.Form):

    merchant_account = forms.ModelChoiceField(queryset=MerchantPaymentAccount.objects.none(), label="Merchant Account")


    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        self.fields['merchant_account'].queryset = MerchantPaymentAccount.objects.filter(account__user=self.user, merchant_user__is_active=True, account__user__is_active=True)

    def clean(self):
        cleaned_data = super().clean()

        merchant_account = cleaned_data['merchant_account']

        selected_account = MerchantPaymentAccount.objects.filter(id=merchant_account.id, merchant_user__is_active=True, account__user__is_active=True).first()

        if selected_account is None:
            raise ValidationError('You cannot remove permissions for this user')

        return cleaned_data

