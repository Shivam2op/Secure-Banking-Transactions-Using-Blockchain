from app.models import Account, MerchantPaymentAccount


def get_payment_accounts(user):
    links = []

    payment_accounts = Account.objects.filter(payment_account__merchant_user=user, user__is_active=True)

    for account in payment_accounts:
        links.append(account.__str__())

    return links


def check_duplicate(user_id, acc_number):
    account = MerchantPaymentAccount.objects.filter(account__acc_number=acc_number, merchant_user_id=user_id, account__user__is_active=True, merchant_user__is_active=True).first()
    if account:
        return True
    return False
