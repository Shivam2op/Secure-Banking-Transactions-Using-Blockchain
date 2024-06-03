from django.contrib.auth import login
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django_otp import DEVICE_ID_SESSION_KEY

from bank import settings
from app.tokens import otp_token_generator, PIITokenGenerator
from django.db import transaction as db_transaction


def help_text_on_hover(fields):
    for field in fields:
        help_text = fields[field].help_text
        fields[field].widget.attrs.update({
            'class': 'help-text-on-hover',
            'data-content': help_text,
        })


def get_unique_acc_number(length=16):
    while True:
        value = get_random_string(length, allowed_chars='0123456789')

        try:
            from app.models import Account

            exist = Account.objects.filter(acc_number=value).count()
        except NameError:
            exist = 0
        except Exception:
            exist = 0

        if exist == 0:
            break

    return value


def get_unique_card_number(length=16):
    while True:
        value = get_random_string(length, allowed_chars='0123456789')

        try:
            from app.models import Card

            exist = Card.objects.filter(card_number=value).count()
        except NameError:
            exist = 0
        except Exception:
            exist = 0

        if exist == 0:
            break

    return value


def send_confirmation_mail(user):
    DEBUG = getattr(settings, 'DEBUG')

    token = otp_token_generator.make_token(user)
    uidb = urlsafe_base64_encode(force_bytes(user.pk)).decode()
    subject = 'Your Account Has Been Created'
    html_message = render_to_string('mail.html', {
        'uidb': uidb,
        'token': token,
        'DEBUG': DEBUG,
    })

    user.email_user(subject, html_message, html_message=html_message)


def send_password_mail(user):
    DEBUG = getattr(settings, 'DEBUG')

    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk)).decode()
    subject = 'Set Account Password'
    html_message = render_to_string('mail_passwordreset.html', {
        'uidb64': uidb64,
        'token': token,
        'DEBUG': DEBUG,
    })

    user.email_user(subject, html_message, html_message=html_message)


def send_transaction_complete_mail(transaction):
    subject = 'Your Transaction Was Completed'

    if transaction.from_account:
        user = transaction.from_account.user
        body = 'Dear %s, your transaction %s was completed.' % (user, transaction)

        user.email_user(subject, body)

    if transaction.to_account:
        user = transaction.to_account.user
        body = 'Dear %s, your transaction %s was completed.' % (user, transaction)

        user.email_user(subject, body)


def send_transaction_declined_mail(transaction):
    subject = 'Your Transaction Was Declined'

    if transaction.from_account:
        user = transaction.from_account.user
        body = 'Dear %s, your transaction %s was declined.' % (user, transaction)

        user.email_user(subject, body)

    if transaction.to_account:
        user = transaction.to_account.user
        body = 'Dear %s, your transaction %s was declined.' % (user, transaction)

        user.email_user(subject, body)


def send_pii_request_mail(from_user, target_user, target_pii):
    DEBUG = getattr(settings, 'DEBUG')
    from_email = getattr(settings, 'EMAIL_HOST_USER')
    pii_token_generator = PIITokenGenerator(target_pii)

    token = pii_token_generator.make_token(from_user)
    uidb1 = urlsafe_base64_encode(force_bytes(from_user.pk)).decode()
    uidb2 = urlsafe_base64_encode(force_bytes(target_user.pk)).decode()

    subject = 'Request For PII Access'
    html_message = render_to_string('pii_access_mail.html', {
        'uidb1': uidb1,
        'uidb2': uidb2,
        'token': token,
        'DEBUG': DEBUG,
        'from_user': from_user,
        'target_user': target_user,
    })

    send_mail(subject, html_message, html_message=html_message, recipient_list=['govt.sbs2018@gmail.com'], from_email=from_email)


def get_pii_link():
    from app.models import MyUser

    users = MyUser.objects.filter(user_type=MyUser.INDIVIDUAL_USER, is_active=True).exclude(username=MyUser.ANON).exclude(is_staff=True).order_by('-date_joined')

    links = []

    for user in users:
        link = reverse('app:Pii', kwargs={
            'user_id': user.id
        })

        links += [
            (user, link)
        ]

    return links

def send_request_approval_mail(user_request):
    user = user_request.from_user

    subject = 'Your Request Was Approved'
    body = 'Dear %s, your request %s was approved.' % (user, user_request)

    user.email_user(subject, body)


def send_request_declined_mail(user_request):
    user = user_request.from_user

    subject = 'Your Request Was Declined'
    body = 'Dear %s, your request %s was declined.' % (user, user_request)

    user.email_user(subject, body)


def get_admin_links():
    links = [
        ('Create User', reverse('app:SignUp')),
        ('View/ Edit Information for all Users', reverse('app:AllUsersView')),
        ('Login As Another User', reverse('app:CustomSuLogin')),

        ('View User PII with permission from Government', reverse('app:ViewPii')),

        ('Views Account Details of External Users', reverse('app:UsersHavingAccountView')),

        ('View User Requests Pending for Approval', reverse('app:UserRequestsReceivedView')),

        ('View All Pending Risky Transactions', reverse('app:TransactionRisky')),

        ('View All Pending Transactions', reverse('app:TransactionPending')),
        ('View All Completed Transactions', reverse('app:TransactionCompleted')),
        ('Transaction Locator', reverse('app:TransactionLocator')),

        ('Initiate User Password Reset', reverse('app:PasswordResetRequestView')),

        ('Reset PKI', reverse('app:PkiView')),

        ('View System Logs', reverse('app:SystemLogsView')),
        ('View Transaction Logs', reverse('app:TransactionLogsView')),

        ('Delete User', reverse('app:UserDelete')),

    ]

    return links


def get_employee_links():
    links = [
        ('View/ Edit Information for External Users', reverse('app:AllUsersView')),

        ('View Account Details of Users Assigned to You', reverse('app:UsersHavingAccountView')),

        ('View User Requests Pending for Approval', reverse('app:UserRequestsReceivedView')),

        ('Create Transaction for External Users', reverse('app:TransactionRequest')),
        ('View Pending Transactions Assigned to You', reverse('app:TransactionPending')),
        ('View All Completed Transactions', reverse('app:TransactionCompleted')),
        ('Transaction Locator', reverse('app:TransactionLocator')),

        ('Reset PKI', reverse('app:PkiView')),
    ]

    return links


def get_manager_links():
    links = [
        ('View/ Edit Information for all External Users', reverse('app:AllUsersView')),

        ('View Accounts Details of Users Assigned to You', reverse('app:UsersHavingAccountView')),

        ('View User Requests Pending for Approval', reverse('app:UserRequestsReceivedView')),

        ('View Pending Transactions Assigned to You', reverse('app:TransactionPending')),

        ('View Pending Risky Transactions Assigned to You', reverse('app:TransactionRisky')),

        ('View All Completed Transactions', reverse('app:TransactionCompleted')),
        ('Transaction Locator', reverse('app:TransactionLocator')),

        ('Reset PKI', reverse('app:PkiView')),
    ]

    return links


def get_merchant_links(user_id):
    links = [
        ('View/ Edit Profile', reverse('app:UserProfile', kwargs={
            'user_id': user_id,
        })),

        ('Credit/ Debit/ Transfer Funds', reverse('app:TransactionRequest')),
        ('Pending Transaction Requests', reverse('app:TransactionPending')),
        ('View Completed Transactions', reverse('app:TransactionCompleted')),
        ('Transaction Locator', reverse('app:TransactionLocator')),

        ('View User Requests Received', reverse('app:UserRequestsReceivedView')),

        ('View Your Accounts/ Balance', reverse('app:UserAccountsView', kwargs={
            'user_id': user_id,
        })),
        ('Request New Account', reverse('app:UserAddAccountView', kwargs={
            'user_id': user_id,
        })),
        ('Enter Known Account', reverse('app:enter_known_account')),
        ('View Known Accounts', reverse('app:view_known_account')),

        ('Enter Client Account', reverse('app:enter_payment_account')),
        ('View Client Accounts', reverse('app:view_payment_account')),
        ('Remove Merchant User Permissions', reverse('app:remove_payment_account')),

        ('Reset PKI', reverse('app:PkiView')),

        ('Delete User', reverse('app:UserDelete')),

    ]

    return links


def get_individual_user_links(user_id):
    links = [
        ('View/ Edit Profile', reverse('app:UserProfile', kwargs={
            'user_id': user_id,
        })),

        ('Credit/ Debit/ Transfer Funds', reverse('app:TransactionRequest')),
        ('Pending Transaction Requests', reverse('app:TransactionPending')),
        ('View Completed Transaction', reverse('app:TransactionCompleted')),
        ('Transaction Locator', reverse('app:TransactionLocator')),

        ('View User Requests Received', reverse('app:UserRequestsReceivedView')),

        ('View Your Accounts/ Balance', reverse('app:UserAccountsView', kwargs={
            'user_id': user_id,
        })),
        ('Request New Account', reverse('app:UserAddAccountView', kwargs={
            'user_id': user_id,
        })),
        ('View PII', reverse('app:Pii', kwargs={
            'user_id': user_id,
        })),
        ('Enter Known Account', reverse('app:enter_known_account')),
        ('View Known Accounts', reverse('app:view_known_account')),
        ('Remove Merchant User Permissions', reverse('app:remove_payment_account')),

        ('Reset PKI', reverse('app:PkiView')),

        ('Delete User', reverse('app:UserDelete')),

    ]

    return links


def is_int_equal(one, two):
    if int(one) == int(two):
        return True

    return False


def login_and_verify_without_otp(request, user, backend=None):
    login(request, user, backend)

    from django_otp.plugins.otp_totp.models import TOTPDevice

    device = TOTPDevice.objects.filter(user=user).first()

    if device:
        request.session[DEVICE_ID_SESSION_KEY] = device.persistent_id


def is_request_duplicate(user_request):
    from app.models import UserRequest

    request = UserRequest.objects.filter(
        from_user=user_request.from_user,
        to_user=user_request.to_user,
        request_type=user_request.request_type,
        model_type=user_request.model_type,
        for_url=user_request.for_url,
        is_approved=False,
    ).first()

    if request:
        return True

    if user_request.request_type == UserRequest.DELETE:
        request = UserRequest.objects.filter(
            from_user=user_request.from_user,
            to_user=user_request.to_user.get_assigned_admin(),
            request_type=UserRequest.COMPLETE_DELETE,
            model_type=user_request.model_type,
            for_url=user_request.for_url,
            is_approved=False,
        ).first()

        if request:
            return True

    if user_request.request_type == UserRequest.UPDATE:
        request = UserRequest.objects.filter(
            from_user=user_request.from_user,
            to_user=user_request.to_user.get_assigned_admin(),
            request_type=UserRequest.COMPLETE_UPDATE,
            model_type=user_request.model_type,
            for_url=user_request.for_url,
            is_approved=False,
        ).first()

        if request:
            return True

    return False


@db_transaction.atomic
def get_user_total_balance(user_id):
    from app.models import Account

    accounts = Account.objects.filter(user_id=user_id).select_for_update()

    balance = 0
    for account in accounts:
        balance += account.balance

    return balance

