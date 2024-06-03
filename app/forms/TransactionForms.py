from django import forms
from django.core.exceptions import ValidationError
from django_filters import FilterSet, NumberFilter, ModelChoiceFilter

from app.forms.LoginForms import MyAuthenticationForm
from app.models import Transaction, Account, MyUser


class ExternalRequestForm(forms.ModelForm):
    pki_token = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Transaction
        fields = ('from_account', 'to_account', 'amount', 'approved_by', 'complete_time', 'pki_token')
        labels = {
            'complete_time': 'Completed at'
        }

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields['to_account'].required = False
        self.fields['from_account'].required = False

        if self.user.is_individual_user():
            self.fields['from_account'].queryset = Account.objects.filter(user=self.user, user__is_active=True)
            to_accounts = Account.objects.filter(known_account__user=self.user, user__is_active=True).exclude(user__username=MyUser.ANON) | Account.objects.filter(user=self.user, user__is_active=True).exclude(user__username=MyUser.ANON)
            self.fields['to_account'].queryset = to_accounts.distinct()

        if self.user.is_merchant():
            self.fields['from_account'].queryset = Account.objects.filter(user=self.user, user__is_active=True) | Account.objects.filter(payment_account__merchant_user=self.user, user__is_active=True).exclude(user__username=MyUser.ANON)
            to_accounts = Account.objects.filter(known_account__user=self.user, user__is_active=True).exclude(user__username=MyUser.ANON) | Account.objects.filter(user=self.user, user__is_active=True).exclude(user__username=MyUser.ANON) | Account.objects.filter(payment_account__merchant_user=self.user, user__is_active=True).exclude(user__username=MyUser.ANON)
            self.fields['to_account'].queryset = to_accounts.distinct()

        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['from_account'].queryset = Account.objects.all().exclude(user__username=MyUser.ANON, user__is_active=True).exclude(user__is_staff=True)

            if instance.is_complete:
                pass
            else:
                self.fields.pop('approved_by')
                self.fields.pop('complete_time')
        else:
            self.fields.pop('approved_by')
            self.fields.pop('complete_time')

    def clean(self):
        cleaned_data = super().clean()

        from_account = cleaned_data['from_account']
        to_account = cleaned_data['to_account']

        if not (from_account or to_account):
            raise ValidationError('Both From and To can not be empty.', code='empty from to')

        if from_account == to_account:
            raise ValidationError('Both From and To can not be same', code='same from to')

        if to_account and self.user != to_account.user and from_account is None and not self.user.is_internal_user():
            raise ValidationError('Cannot credit to someone else account')

        if from_account and self.user != from_account.user and self.user.is_individual_user():
            raise ValidationError('Cannot transfer from someone else account')

        return cleaned_data

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        from_account = self.cleaned_data['from_account']

        if amount < 0:
            raise ValidationError('Negative Amount', code='negative amount')

        if amount == 0:
            raise ValidationError('Zero Amount', code='zero amount')

        if from_account and from_account.balance < amount:
            raise ValidationError('Low Balance', code='low balance')

        return amount


class InternalRequestForm(ExternalRequestForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(user, *args, **kwargs)

        self.fields['from_account'].queryset = Account.objects.all().exclude(user__username=MyUser.ANON, user__is_active=True).exclude(user__is_staff=True)
        self.fields['to_account'].queryset = Account.objects.all().exclude(user__username=MyUser.ANON, user__is_active=True).exclude(user__is_staff=True)


class VerifyOTPForm(MyAuthenticationForm):

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        self.fields.pop('username')
        self.fields.pop('password')

    def get_user(self):
        user = self.request.user

        return user


def filter_account_based_on_user_from(request):
    if request is None:
        return Account.objects.none()

    user = request.user

    if user.is_internal_user():
        return Account.objects.all().exclude(user__username=MyUser.ANON).exclude(user__is_staff=True)

    elif user.is_individual_user():
        return Account.objects.filter(user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True)

    elif user.is_merchant():
        return Account.objects.filter(payment_account__merchant_user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True) | Account.objects.filter(user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True)

    else:
        return Account.objects.none()


def filter_account_based_on_user_to(request):
    if request is None:
        return Account.objects.none()

    user = request.user

    if user.is_internal_user():
        return Account.objects.all().exclude(user__username=MyUser.ANON).exclude(user__is_staff=True)

    elif user.is_individual_user():
        return (Account.objects.filter(user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True) | Account.objects.filter(known_account__user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True)).distinct()

    elif user.is_merchant():
        return (Account.objects.filter(payment_account__merchant_user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True) | Account.objects.filter(user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True) | Account.objects.filter(known_account__user=user).exclude(user__username=MyUser.ANON).exclude(user__is_staff=True)).distinct()

    else:
        return Account.objects.none()


def get_transaction_queryset(user):
    queryset = Transaction.objects.none()

    if user.is_internal_user():
        queryset = Transaction.objects.filter(is_approved=True) | Transaction.objects.filter(is_approved=False, from_account__user__is_active=True) | Transaction.objects.filter(is_approved=False, to_account__user__is_active=True)

    elif user.is_individual_user():
        queryset = Transaction.objects.filter(from_account__user=user) | Transaction.objects.filter(to_account__user=user)
        queryset = queryset.filter(is_approved=True) | queryset.filter(is_approved=False, from_acount__user__is_active=True) | queryset.filter(is_approved=False, to_account__user__is_active=True)

    elif user.is_merchant():
        queryset = Transaction.objects.filter(from_account__user=user) | Transaction.objects.filter(to_account__user=user) | Transaction.objects.filter(to_account__payment_account__merchant_user=user) | Transaction.objects.filter(from_account__payment_account__merchant_user=user)
        queryset = queryset.filter(is_approved=True) | queryset.filter(is_approved=False, from_acount__user__is_active=True) | queryset.filter(is_approved=False, to_account__user__is_active=True) | queryset.filter(is_approved=False, from_account__payment_account__merchant_user__is_active=True) | queryset.filter(is_approved=False, to_account__payment_account__merchant_user__is_active=True)

    return queryset.distinct()


class TransactionLocatorForm(FilterSet):
    amount__gt = NumberFilter(field_name='amount', lookup_expr='gt')
    amount__lte = NumberFilter(field_name='amount', lookup_expr='lte')

    from_account = ModelChoiceFilter(queryset=filter_account_based_on_user_from)
    to_account = ModelChoiceFilter(queryset=filter_account_based_on_user_to)

    class Meta:
        model = Transaction
        fields = ('id', 'from_account', 'to_account', 'amount__gt', 'amount__lte', 'is_complete')
