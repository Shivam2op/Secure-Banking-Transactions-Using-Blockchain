from django import forms

from app.models import Account


class UserAccountForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ('acc_number', 'balance')
