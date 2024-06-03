from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from app.models import *


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = MyUser


class MyUserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = MyUser
