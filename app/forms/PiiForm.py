from django import forms

from app.models import PII


class PiiForm(forms.ModelForm):
    aadhar = forms.RegexField(
        regex=r'^\d{12}$',
        widget=forms.TextInput(),
        error_messages={
            'invalid': 'Enter a valid aadhar number. Must be 12 digits.'
        }
    )

    class Meta:
        model = PII
        fields = ('aadhar',)
        labels = {
            'aadhar': "Aadhar Number"
        }

