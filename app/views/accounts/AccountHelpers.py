from django.urls import reverse

from app.models import MyUser, Account


def get_user_accounts(user_id):
    user = MyUser.objects.filter(id=user_id, user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT), is_active=True).exclude(username=MyUser.ANON).first()

    links = []

    if user:
        accounts = Account.objects.filter(user=user)

        for account in accounts:
            links += [
                (account.__str__(), reverse('app:AccountView', kwargs={
                    'user_id': user_id,
                    'account_id': account.id,
                }))
            ]

        return links

    return links


def get_account(user_id, account_id):
    account = Account.objects.filter(user_id=user_id, id=account_id, user__user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT), user__is_active=True).exclude(user__username=MyUser.ANON).first()

    return account


def get_users_having_accounts():
    users_with_account = MyUser.objects.filter(user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT), is_active=True).exclude(username=MyUser.ANON)

    links = []

    for user in users_with_account:
        links += [
            (user.username, reverse('app:UserAccountsView', kwargs={
                'user_id': user.id,
            }))
        ]

    return links


def is_user_having_account(user_id):
    accounts = Account.objects.filter(user__user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT), user_id=user_id,  user__is_active=True).exclude(user__username=MyUser.ANON).first()

    if accounts:
        return True

    return False


def create_account_for_user(user):
    Account.objects.create(user=user)


def get_users_assigned_to_manager_employee(assigned_user):
    users_list = []

    if assigned_user.is_manager():
        users_list = MyUser.objects.filter(assigned_to__assigned_to=assigned_user,  is_active=True).exclude(username=MyUser.ANON)

    if assigned_user.is_employee():
        users_list = MyUser.objects.filter(assigned_to=assigned_user,  is_active=True).exclude(username=MyUser.ANON)

    links = []

    for user in users_list:
        links += [
            (user.username, reverse('app:UserAccountsView', kwargs={
                'user_id': user.id,
            }))
        ]

    return links


def get_user_assigned_accounts(target_user_id, assigned_user):
    user = []

    if assigned_user.is_employee():
        user = MyUser.objects.filter(id=target_user_id, assigned_to=assigned_user, is_active=True, user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT)).exclude(username=MyUser.ANON).first()

    if assigned_user.is_manager():
        user = MyUser.objects.filter(id=target_user_id, assigned_to__assigned_to=assigned_user,  is_active=True, user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT)).exclude(username=MyUser.ANON).first()

    links = []

    if user:
        accounts = Account.objects.filter(user=user)

        for account in accounts:
            links += [
                (account.__str__(), reverse('app:AccountView', kwargs={
                    'user_id': target_user_id,
                    'account_id': account.id,
                }))
            ]

        return links

    return links


def get_assigned_account_details(target_user_id, account_id, assigned_user):
    account = []

    if assigned_user.is_employee():
        account = Account.objects.filter(user__assigned_to=assigned_user, user__is_active=True, user_id=target_user_id, id=account_id, user__user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT)).exclude(
            user__username=MyUser.ANON).first()

    if assigned_user.is_manager():
        account = Account.objects.filter(user__assigned_to__assigned_to=assigned_user, user__is_active=True, user_id=target_user_id, id=account_id, user__user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT)).exclude(
            user__username=MyUser.ANON).first()

    return account
