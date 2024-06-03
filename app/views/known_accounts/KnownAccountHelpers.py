from app.models import Account, KnownAccount


def check_duplicate(user_id, acc_number):
    account = KnownAccount.objects.filter(account__acc_number=acc_number, user_id=user_id, user__is_active=True, account__user__is_active=True).first()
    if account:
        return True
    return False


def get_account_from_number(acc_number):
    account = Account.objects.filter(acc_number=acc_number, user__is_active=True).first()

    return account


def check_same_user_account(user_id, acc_number):
    account = Account.objects.filter(acc_number=acc_number,  user_id=user_id, user__is_active=True).first()

    if account:
        return True
    else:
        return False


def get_known_accounts(user):
    links = []

    known_accounts = Account.objects.filter(user=user, user__is_active=True) | Account.objects.filter(known_account__user=user, user__is_active=True, known_account__user__is_active=True)

    for account in known_accounts.distinct():
        links.append(account.__str__())

    return links
