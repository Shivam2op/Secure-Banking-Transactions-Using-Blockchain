from django import forms

from app.models import UserRequest, MyUser


class CreateRequestForm(forms.ModelForm):

    class Meta:
        model = UserRequest
        fields = ('request_type', 'model_type')
        labels = {
            'request_type': 'Type',
            'model_type': 'For',
        }


class RequestForm(forms.ModelForm):

    class Meta:
        model = UserRequest
        fields = ('from_user', 'to_user', 'request_type', 'model_type', 'for_url')
        labels = {
            'request_type': 'Type',
            'model_type': 'For',
            'for_url': 'To Access'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['from_user'].queryset = MyUser.objects.filter(is_active=True).exclude(username=MyUser.ANON).exclude(is_staff=True)
        self.fields['to_user'].queryset = MyUser.objects.filter(is_active=True).exclude(username=MyUser.ANON).exclude(is_staff=True)

        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields.pop('to_user')

            if instance.request_type == UserRequest.COMPLETE_UPDATE:
                self.fields.pop('for_url')

            elif instance.request_type == UserRequest.DELETE:
                self.fields.pop('for_url')

        else:
            self.fields.pop('from_user')

    # TODO: From_user and To_user validation
