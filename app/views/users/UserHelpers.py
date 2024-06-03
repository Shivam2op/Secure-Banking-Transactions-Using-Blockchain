import random

from django.urls import reverse
from guardian.models import UserObjectPermission

from app.forms.RequestForms import RequestForm
from app.models import MyUser, UserRequest, EditUser, Account, Transaction, \
    KnownAccount, MerchantPaymentAccount
from app.views.accounts import AccountHelpers


def get_users(internal_too=False):
    users = MyUser.objects.filter(user_type__in=(MyUser.MERCHANT, MyUser.INDIVIDUAL_USER), is_active=True).exclude(username=MyUser.ANON).exclude(is_staff=True).order_by('-date_joined')

    if internal_too:
        users = MyUser.objects.filter(is_active=True).exclude(username=MyUser.ANON).exclude(is_staff=True).order_by('-date_joined')

    links = []

    for user in users:
        link = reverse('app:UserProfile', kwargs={
            'user_id': user.id
        })

        links += [
            (user, link)
        ]

    return links


def get_unapproved_user_requests_to_user(user):
    user_requests = UserRequest.objects.filter(to_user=user, is_approved=False, to_user__is_active=True, from_user__is_active=True)
    links = []

    for user_request in user_requests:
        link = reverse('app:UserRequestView', kwargs={
            'user_request_id': user_request.id,
        })

        links += [
            (user_request, link)
        ]

    return links


def get_user_request_to_user_using_id(user_request_id, user):
    user_request = UserRequest.objects.filter(id=user_request_id, to_user=user, to_user__is_active=True, from_user__is_active=True).select_for_update().first()

    return user_request


def assign_permissions(user_request):
    request_type = user_request.request_type
    model_type = user_request.model_type
    assign_to = user_request.from_user

    if request_type == UserRequest.READ:
        if model_type == UserRequest.USER:
            user_obj = user_request.user_obj
            UserObjectPermission.objects.assign_perm('read_user', assign_to, user_obj)

        elif model_type == UserRequest.ACCOUNT:
            account_obj = user_request.account_obj
            UserObjectPermission.objects.assign_perm('read_account', assign_to, account_obj)

        elif model_type == UserRequest.TRANSACTION:
            transaction_obj = user_request.transaction_obj
            UserObjectPermission.objects.assign_perm('read_transaction', assign_to, transaction_obj)

        elif model_type == UserRequest.PII_ACCESS:
            pii_obj = user_request.pii_obj
            UserObjectPermission.objects.assign_perm('read_pii', assign_to, pii_obj)

        else:
            return False

    elif request_type == UserRequest.CREATE:
        if model_type == UserRequest.ACCOUNT:
            if user_request.account_obj:
                MerchantPaymentAccount.objects.create(merchant_user=user_request.from_user, account=user_request.account_obj)

            else:
                AccountHelpers.create_account_for_user(assign_to)
        else:
            return False

    elif request_type == UserRequest.UPDATE:
        if model_type == UserRequest.USER:
            user_obj = user_request.user_obj
            UserObjectPermission.objects.assign_perm('edit_user', assign_to, user_obj)

        else:
            return False

    elif request_type == UserRequest.DELETE:
        if model_type == UserRequest.USER:
            user_obj = user_request.user_obj

            form = RequestForm(data={
                'to_user': assign_to.get_assigned_admin().id,
                'request_type': UserRequest.COMPLETE_DELETE,
                'model_type': UserRequest.USER,
            })

            if form.is_valid():
                new_request = form.save(commit=False)
                new_request.from_user = assign_to
                new_request.user_obj = user_obj
                new_request.save()

            else:
                return False

        else:
            return False

    elif request_type == UserRequest.COMPLETE_UPDATE:
        if model_type == UserRequest.USER:
            user_obj = user_request.user_obj
            edit_user = get_edited_user(user_obj)

            if edit_user:
                update_user_from_edited_version(edit_user)

            else:
                return False

        else:
            return False

    elif request_type == UserRequest.COMPLETE_DELETE:
        if model_type == UserRequest.USER:
            user_obj = user_request.user_obj

            delete_request_from_external_user = UserRequest.objects.filter(is_approved=True, model_type=UserRequest.USER, request_type=UserRequest.DELETE, from_user=user_obj, user_obj=user_obj).count()
            complete_delete_request_related = UserRequest.objects.filter(is_approved=True, model_type=UserRequest.USER, request_type=UserRequest.COMPLETE_DELETE, user_obj=user_obj).count()

            # Handle case that an internal user cannot raise request to delete external user without consent
            if delete_request_from_external_user > 0:
                if delete_request_from_external_user == complete_delete_request_related + 1:
                    if not safely_delete_user(user_obj):
                        return False

                else:
                    return False

            else:
                return False

        else:
            return False

    else:
        return False

    return True


def delete_request(user_request):
    if user_request.request_type == UserRequest.COMPLETE_UPDATE:
        EditUser.objects.filter(user=user_request.user_obj).select_for_update().delete()

    UserRequest.objects.filter(id=user_request.id, is_approved=False).select_for_update().delete()


def get_edited_user(user):
    return EditUser.objects.filter(user=user).first()


def update_user_from_edited_version(edited_user):
    user = edited_user.user

    user.first_name = edited_user.first_name
    user.last_name = edited_user.last_name
    user.email = edited_user.email
    user.phone_number = edited_user.phone_number
    user.date_of_birth = edited_user.date_of_birth

    user.save()
    edited_user.delete()


def can_user_be_deleted(user):

    if user.is_individual_user() or user.is_merchant():
        pending_transactions = Transaction.objects.filter(is_approved=False, from_account__user=user).count()

        if pending_transactions > 0:
            return False

        return True

    elif user.is_employee():
        manager = user.get_assigned_manager()
        employee_count = MyUser.objects.filter(is_active=True, assigned_to=manager).count()

        if employee_count == 1:
            assigned_users = MyUser.objects.filter(is_active=True, assigned_to=user).count()

            if assigned_users > 0:
                return False

        return True

    elif user.is_manager():
        admin = user.get_assigned_admin()
        manager_count = MyUser.objects.filter(is_active=True, assigned_to=admin).count()

        if manager_count == 1:
            assigned_users = MyUser.objects.filter(is_active=True, assigned_to=user).count()

            if assigned_users > 0:
                return False

        return True

    else:
        return False


def safely_delete_user(user):
    if not can_user_be_deleted(user):
        return False

    if user.is_individual_user() or user.is_merchant():
        accounts = Account.objects.filter(user=user).select_for_update()

        for account in accounts:
            account.balance = 0
            account.save()

        pending_transactions = Transaction.objects.filter(is_approved=False)
        pending_transactions = pending_transactions.filter(to_account__user=user)
        pending_transactions = pending_transactions.select_for_update()
        pending_transactions.delete()

        pending_requests = UserRequest.objects.filter(is_approved=False)
        pending_requests = pending_requests.filter(from_user=user) | pending_requests.filter(to_user=user)
        pending_requests = pending_requests.select_for_update()
        pending_requests.delete()

        client_accounts_of_user = MerchantPaymentAccount.objects.filter(account__user=user).select_for_update()
        client_accounts_of_user.delete()

        known_accounts_of_user = KnownAccount.objects.filter(user=user).select_for_update()
        known_accounts_of_user.delete()

        user.is_active = False
        user.save()

        return True

    elif user.is_employee():
        manager = user.get_assigned_manager()
        temp_employees = MyUser.objects.filter(is_active=True, assigned_to=manager)

        employees = []
        for employee in temp_employees:
            if employee == user:
                continue

            employees += [employee]

        assigned_users = MyUser.objects.filter(is_active=True, assigned_to=user)
        for assigned_user in assigned_users:
            index = random.randint(0, len(employees)-1)

            assigned_user.assigned_to = employees[index]
            assigned_user.save()

        pending_requests = UserRequest.objects.filter(is_approved=False)
        pending_requests = pending_requests.filter(from_user=user) | pending_requests.filter(to_user=user)
        pending_requests = pending_requests.select_for_update()
        pending_requests.delete()

        user.is_active = False
        user.save()

        return True

    elif user.is_manager():
        admin = user.get_assigned_admin()
        temp_managers = MyUser.objects.filter(is_active=True, assigned_to=admin)

        managers = []
        for manager in temp_managers:
            if manager == user:
                continue

            managers += [manager]

        assigned_users = MyUser.objects.filter(is_active=True, assigned_to=user)
        for assigned_user in assigned_users:
            index = random.randint(0, len(managers)-1)

            assigned_user.assigned_to = managers[index]
            assigned_user.save()

        pending_requests = UserRequest.objects.filter(is_approved=False)
        pending_requests = pending_requests.filter(from_user=user) | pending_requests.filter(to_user=user)
        pending_requests = pending_requests.select_for_update()
        pending_requests.delete()

        user.is_active = False
        user.save()

        return True

    else:
        return False
