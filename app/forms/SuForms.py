from django import forms
from django.core.exceptions import ValidationError
from django_su.forms import UserSuForm

from app.models import MyUser


class MyUserSuForm(UserSuForm):
    user = forms.ModelChoiceField(queryset=MyUser.objects.filter(is_active=True).exclude(username=MyUser.ANON).exclude(user_type=MyUser.ADMIN))

    def clean(self):
        cleaned_data = super().clean()

        user = cleaned_data['user']
        selected_user = MyUser.objects.filter(id=user.id).exclude(username=MyUser.ANON).exclude(user_type=MyUser.ADMIN).first()

        if selected_user is None:
            raise ValidationError('You cannot switch into this user')

        return cleaned_data
