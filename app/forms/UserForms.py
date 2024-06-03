from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from app.models import MyUser, EditUser
from app.views.users import UserHelpers


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = MyUser
        fields = ('first_name', 'last_name', 'username', 'email', 'phone_number', 'date_of_birth', 'date_joined')

    def __init__(self, user_id, *args, **kwargs):
        self.user_id = user_id
        super().__init__(*args, **kwargs)


class EditUserProfileForm(forms.ModelForm):

    years = []
    for year in range(2018, 1900, -1):
        years += [year]

    date_of_birth = forms.DateField(
        widget=forms.SelectDateWidget(
            years=years,
        ),
        label='Date Of Birth',
    )

    class Meta:
        model = EditUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')

    def __init__(self, user_id, *args, **kwargs):
        self.user_id = user_id
        super().__init__(*args, **kwargs)

    def clean_date_of_birth(self):
        data = self.cleaned_data['date_of_birth']

        if data > datetime.now().date():
            raise ValidationError('Future Date Invalid', code='future date')

        return data

    def clean(self):
        cleaned_data = super().clean()

        user = MyUser.objects.filter(id=self.user_id).first()

        if user:
            if user.first_name == cleaned_data['first_name'] and user.last_name == cleaned_data['last_name']:
                if user.phone_number == cleaned_data['phone_number'] and user.date_of_birth == cleaned_data['date_of_birth']:
                    if user.email == cleaned_data['email']:
                        raise ValidationError('No changes observed')

        return cleaned_data


class UserDeleteForm(forms.Form):
    user = forms.ModelChoiceField(queryset=MyUser.objects.filter(is_active=True, user_type__in=(MyUser.EMPLOYEE, MyUser.MANAGER)).exclude(username=MyUser.ANON))

    def clean(self):
        cleaned_data = super().clean()

        user = cleaned_data['user']
        selected_user = MyUser.objects.filter(id=user.id, is_active=True, user_type__in=(MyUser.EMPLOYEE, MyUser.MANAGER)).exclude(username=MyUser.ANON).first()

        if selected_user is None:
            raise ValidationError('You cannot delete this user')

        if not UserHelpers.can_user_be_deleted(user):
            raise ValidationError('This user cannot be deleted at the moment')

        return cleaned_data
