from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.db import models
from datetime import datetime

from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice
from app.views import CommonHelpers
from app.views.CommonHelpers import get_unique_acc_number, get_unique_card_number


class MyUserManager(BaseUserManager):
    def create_user(self, username, email, password, user_type, first_name='', last_name='', phone_number=None,
                    date_of_birth=None, validate=True, is_active=False, send_password_mail=True, send_otp_mail=False, created_by=None):

        if not email or not username:
            raise ValueError('Users must have an email and a username')

        if password is None:
            password = self.make_random_password()
            validate = False

        username = username.lower()

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
            username=username,
            phone_number=phone_number,
            date_of_birth=date_of_birth,
            user_type=user_type,
            assigned_to=created_by,
        )

        if validate:
            validate_password(password)
        user.set_password(password)

        # Activate User on email confirmation, bypass for superuser
        user.is_active = is_active

        user.save(using=self.db)

        TOTPDevice.objects.create(name='Phone', user=user, confirmed=False)

        if not user.is_internal_user():
            account = Account.objects.create(user=user)
            Card.objects.create(account=account)

        if send_password_mail:
            CommonHelpers.send_password_mail(user)

        if send_otp_mail:
            CommonHelpers.send_confirmation_mail(user)

        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password=password, user_type=MyUser.ADMIN, validate=False,
                                send_password_mail=False, send_otp_mail=True, is_active=True)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self.db)
        return user

    # Make username case insensitive
    def get_by_natural_key(self, username):
        return self.get(username__iexact=username)


# Unused
class Address(models.Model):
    house = models.TextField('house address', max_length=100)
    street = models.TextField('street address', max_length=500)
    city = models.CharField(max_length=100)
    zip = models.CharField(max_length=6)

    def __str__(self):
        return self.house + ', ' + self.street


class MyUser(AbstractUser):
    phone_number = models.CharField(null=True, blank=True, max_length=10)
    date_of_birth = models.DateField(null=True, blank=True)

    ADMIN = 5
    MANAGER = 4
    EMPLOYEE = 3
    MERCHANT = 2
    INDIVIDUAL_USER = 1
    USER_TYPE_CHOICES = (
        (INDIVIDUAL_USER, 'Individual User'),
        (MERCHANT, 'Merchant'),
        (EMPLOYEE, 'Employee'),
        (MANAGER, 'Manager'),
        (ADMIN, 'Admin'),
    )

    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=INDIVIDUAL_USER)

    assigned_to = models.ForeignKey('self', on_delete=models.CASCADE, related_name='assigned_user', null=True, blank=True)

    email = models.EmailField('Email Address', unique=False)

    objects = MyUserManager()

    # Django-guardian AnonymousUser
    ANON = 'AnonymousUser'

    class Meta:
        permissions = (
            ('read_user', 'Read User'),
            ('edit_user', 'Edit User'),
        )

    def is_admin(self):
        return int(self.user_type) == MyUser.ADMIN

    def is_manager(self):
        return int(self.user_type) == MyUser.MANAGER

    def is_employee(self):
        return int(self.user_type) == MyUser.EMPLOYEE

    def is_merchant(self):
        return int(self.user_type) == MyUser.MERCHANT

    def is_individual_user(self):
        return int(self.user_type) == MyUser.INDIVIDUAL_USER

    def is_internal_user(self):
        return not (self.is_individual_user() or self.is_merchant())

    def get_hidden_phone_number(self):
        return '*' * 7 + self.phone_number[-3:]

    def get_assigned_manager(self):
        if self.is_internal_user():
            if self.is_employee():
                return self.assigned_to
            return None

        return self.assigned_to.assigned_to

    def get_assigned_admin(self):
        if self.is_internal_user():
            if self.is_employee():
                return self.assigned_to.assigned_to
            elif self.is_manager():
                return self.assigned_to
            return None

        return self.assigned_to.assigned_to.assigned_to


class Account(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='acc_user', null=True, limit_choices_to={
        'user_type__in': (MyUser.INDIVIDUAL_USER, MyUser.MERCHANT),
    })

    acc_number = models.CharField('Account Number', max_length=16, unique=True, default=get_unique_acc_number)
    balance = models.PositiveIntegerField(default=0)

    class Meta:
        permissions = (
            ('read_account', 'Read Account'),
        )

    def get_hidden_account_number(self):
        return '*' * 12 + self.acc_number[-4:]

    def __str__(self):
        return self.user.username + ', ' + self.get_hidden_account_number()

    def save(self, *args, **kwargs):
        if self.user.username == MyUser.ANON:
            raise Exception('AnonymousUser can not have an Account')

        if self.user.is_internal_user():
            raise Exception('Internal User can not have an Account')

        return super(Account, self).save(*args, **kwargs)


class Card(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='acc_card')
    card_number = models.CharField(max_length=16, unique=True, default=get_unique_card_number)

    def __str__(self):
        return self.card_number


class PII(models.Model):
    user = models.OneToOneField(MyUser, null=False, on_delete=models.CASCADE, related_name='pii_user')
    aadhar = models.CharField('aadhar number', unique=True, max_length=12)

    def __str__(self):
        return self.aadhar

    class Meta:
        permissions = (
            ('read_pii', 'Read PII'),
        )


class Transaction(models.Model):
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transaction_from', null=True,
                                     blank=True)
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transaction_to', null=True,
                                   blank=True)

    created_by = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=False, related_name='transaction_creator')

    amount = models.PositiveIntegerField(default=0)

    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='approved_transaction')

    is_complete = models.BooleanField(default=False)

    request_time = models.DateTimeField(default=timezone.now)
    complete_time = models.DateTimeField(null=True, blank=True)

    RISKY_LIMIT = 100000

    class Meta:
        permissions = (
            ('read_transaction', 'Read Transaction'),
            ('edit_transaction', 'Edit Transaction'),
        )

    def is_risky(self):
        return self.amount > self.RISKY_LIMIT

    def approve(self, user):
        self.is_approved = True
        self.approved_by = user
        self.save()

    def complete(self):
        self.is_complete = True
        self.complete_time = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if not (self.from_account or self.to_account):
            raise Exception('One of From or To are required')

        if self.from_account and self.to_account and self.from_account.id == self.to_account.id:
            raise Exception('From and To can not be the same')

        if self.is_complete and not self.is_approved:
            raise Exception('Cannot complete unapproved transaction')

        if self.to_account and self.created_by != self.to_account.user and self.from_account is None and not self.created_by.is_internal_user():
            raise Exception('Cannot credit to someone else account')

        if self.from_account and self.created_by != self.from_account.user and self.created_by.is_individual_user():
            raise Exception('Cannot transfer from someone else account')

        if self.is_approved:
            if self.approved_by:
                if self.is_risky() and (
                        not self.approved_by.is_internal_user() or self.approved_by.is_employee()):
                    raise Exception('User not authorised to perform this transaction')
            else:
                raise Exception('Approved By not set')

        return super(Transaction, self).save(*args, **kwargs)

    def __str__(self):
        return 'Transaction ID: ' + str(
            self.id) + ', Created By: ' + self.created_by.__str__() + ', At: ' + timezone.localtime(
            self.request_time).strftime('%d-%m-%Y %H:%M')


class UserRequest(models.Model):
    from_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='request_from')
    to_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='request_to', null=True, blank=True)

    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4
    COMPLETE_UPDATE = 5
    COMPLETE_DELETE = 6
    USER_REQUEST_CHOICES = (
        (CREATE, 'Create'),
        (READ, 'Read'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
        (COMPLETE_UPDATE, 'Complete Update'),
        (COMPLETE_DELETE, 'Complete Delete'),
    )

    ACCOUNT = 1
    TRANSACTION = 2
    USER = 3
    PII_ACCESS = 4
    TYPE_CHOICES = (
        (ACCOUNT, 'Account'),
        (TRANSACTION, 'Transaction'),
        (USER, 'User Profile'),
        (PII_ACCESS, 'PII')
    )

    for_url = models.URLField(null=True, blank=True)

    request_type = models.PositiveSmallIntegerField(choices=USER_REQUEST_CHOICES, null=True, blank=True)

    model_type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, null=True, blank=True)

    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True, blank=True, related_name='approved_request')

    account_obj = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='user_request_account', null=True, blank=True)
    transaction_obj = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='user_request_transaction', null=True, blank=True)
    user_obj = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='user_request_user_obj', null=True, blank=True)
    pii_obj = models.ForeignKey(PII, on_delete=models.CASCADE, related_name='user_request_pii', null=True, blank=True)

    def approve(self, user):
        self.is_approved = True
        self.approved_by = user
        self.save()

    def save(self, *args, **kwargs):
        if not (self.from_user or self.to_user):
            raise Exception('One of From or To are required')

        if self.from_user and self.to_user and self.from_user.id == self.to_user.id:
            raise Exception('From and To can not be the same')

        if self.is_approved:
            if self.approved_by:
                pass
            else:
                raise Exception('Approved By not set')

        return super(UserRequest, self).save(*args, **kwargs)

    def __str__(self):
        return 'From ' + self.from_user.__str__() + ' to ' + dict(self.USER_REQUEST_CHOICES).get(
            self.request_type) + ' ' + dict(self.TYPE_CHOICES).get(self.model_type)


class KnownAccount(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='known_user', limit_choices_to={
        'user_type__in': (MyUser.INDIVIDUAL_USER, MyUser.MERCHANT),
    })
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='known_account')

    class Meta:
        unique_together = ('user', 'account',)

    def __str__(self):
        return "User : " + self.user.username + " Known Account : " + self.account.acc_number


class MerchantPaymentAccount(models.Model):
    merchant_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='merchant_user', limit_choices_to={
        'user_type': MyUser.MERCHANT,
    })
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='payment_account')

    class Meta:
        unique_together = ('merchant_user', 'account',)

    def __str__(self):
        return "Merchant User : " + self.merchant_user.username + " Payment Account : " + self.account.get_hidden_account_number()


class PublicKey(models.Model):
    user = models.ForeignKey(MyUser, null=False, on_delete=models.CASCADE, related_name='publickey_user')
    publickey = models.CharField('public key', max_length=255, unique=True)

    def __str__(self):
        return self.publickey


class EditUser(models.Model):
    user = models.ForeignKey(MyUser, null=False, on_delete=models.CASCADE, related_name='edited_user')

    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField('Email Address', unique=False)
    phone_number = models.CharField(null=True, blank=True, max_length=10)
    date_of_birth = models.DateField(null=True, blank=True)
