from django import forms

from app.models import PublicKey


class PKIForms(forms.ModelForm):

    class Meta:
        model = PublicKey
        fields = ('publickey',)
        labels = {
            'publickey': "Public Key"
        }
