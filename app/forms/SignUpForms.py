import random

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from app.models import *
from app.views import CommonHelpers


class PersonalInfo(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(
        attrs={'autofocus': ''}),
        label='First Name',
    )

    phone_number = forms.RegexField(
        regex=r'^\d{10}$',
        widget=forms.TextInput(),
        error_messages={
            'invalid': 'Enter a valid phone number. Must be 10 digits.'
        }
    )

    confirm_email = forms.EmailField(label='Confirm Email')

    years = []
    for year in range(2018, 1900, -1):
        years += [year]

    date_of_birth = forms.DateField(
        widget=forms.SelectDateWidget(
            years=years,
        ),
        label='Date Of Birth',
    )

    USER_TYPE_CHOICES = MyUser.USER_TYPE_CHOICES

    user_type = forms.ChoiceField(widget=forms.RadioSelect, choices=USER_TYPE_CHOICES)

    def __init__(self, created_by, *args, **kwargs):
        self.created_by = created_by

        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields.pop('password1')
        self.fields.pop('password2')
        CommonHelpers.help_text_on_hover(self.fields)

    class Meta:
        model = MyUser
        fields = ('first_name', 'last_name', 'username', 'email', 'confirm_email', 'phone_number', 'date_of_birth', 'user_type')
        labels = {
            'last_name': 'Last Name',
            'phone_number': 'Phone Number',
            'email': 'Email Address',
        }

    def clean_date_of_birth(self):
        data = self.cleaned_data['date_of_birth']

        if data > datetime.now().date():
            raise ValidationError('Future Date Invalid', code='future date')

        return data

    def clean_confirm_email(self):
        email1 = self.cleaned_data['email']
        email2 = self.cleaned_data['confirm_email']

        if email1 and email2 and email1 != email2:
            raise ValidationError('Email Does Not Match', code='match email')

        return email2

    def clean_user_type(self):
        user_type = self.cleaned_data['user_type']

        if CommonHelpers.is_int_equal(user_type, MyUser.ADMIN):
            self.created_by = None

        elif CommonHelpers.is_int_equal(user_type, MyUser.EMPLOYEE):
            managers = MyUser.objects.filter(assigned_to=self.created_by, user_type=MyUser.MANAGER)

            if managers:
                index = random.randint(0, len(managers)-1)

                manager = managers[index]
                self.created_by = manager
            else:
                raise ValidationError('Managers do not exist')

        elif CommonHelpers.is_int_equal(user_type, MyUser.INDIVIDUAL_USER) or CommonHelpers.is_int_equal(user_type, MyUser.MERCHANT):
            managers = MyUser.objects.filter(assigned_to=self.created_by, user_type=MyUser.MANAGER)

            temp_managers = []
            for manager in managers:
                employees = MyUser.objects.filter(assigned_to=manager, user_type=MyUser.EMPLOYEE).count()
                if employees > 0:
                    temp_managers += [manager]

            managers = temp_managers

            if managers:
                index = random.randint(0, len(managers)-1)

                manager = managers[index]
                employees = MyUser.objects.filter(assigned_to=manager, user_type=MyUser.EMPLOYEE)

                if employees:
                    index = random.randint(0, len(employees)-1)

                    employee = employees[index]
                    self.created_by = employee
                else:
                    raise ValidationError('Employees do not exist')
            else:
                raise ValidationError('Managers do not exist')

        return user_type

    def save(self, commit=True):
        user = MyUser.objects.create_user(
            self.cleaned_data['username'],
            self.cleaned_data['email'],
            None,
            self.cleaned_data['user_type'],
            self.cleaned_data['first_name'],
            self.cleaned_data['last_name'],
            self.cleaned_data['phone_number'],
            self.cleaned_data['date_of_birth'],
            created_by=self.created_by
        )

        if commit:
            user.save()

        return user


# Unused
class AddressInfo(forms.ModelForm):

    class Meta:
        model = Address
        fields = '__all__'
        labels = {
            'zip': 'Zip Code',
            'house': 'House Address',
            'street': 'Street Address',
        }
        widgets = {
            'house': forms.TextInput(),
            'street': forms.TextInput(),
        }

    def save(self, commit=True):
        address, created = Address.objects.get_or_create(
            house=self.cleaned_data['house'],
            street=self.cleaned_data['street'],
            city=self.cleaned_data['city'],
            zip=self.cleaned_data['zip'],
        )

        if commit:
            address.save()

        return address


class PasswordResetRequestForm(forms.Form):

    user = forms.ModelChoiceField(queryset=MyUser.objects.all().exclude(username=MyUser.ANON).exclude(is_staff=True))
