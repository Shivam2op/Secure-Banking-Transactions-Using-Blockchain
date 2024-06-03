from django.urls import reverse
from app.models import Transaction, Account
from django.db import transaction as db_transaction


@db_transaction.atomic
def perform_transaction(transaction):
    from_account = transaction.from_account
    to_account = transaction.to_account
    amount = transaction.amount

    transaction = Transaction.objects.filter(id=transaction.id, is_approved=False).select_for_update().first()

    if transaction is None:
        return False

    if from_account:
        from_account = Account.objects.filter(id=from_account.id).select_for_update().first()
        from_account.balance -= amount
        if from_account.balance < 0:
            return False
        from_account.save()
    if to_account:
        to_account = Account.objects.filter(id=to_account.id).select_for_update().first()
        to_account.balance += amount
        to_account.save()

    return True


def get_pending_transactions_assigned_to_user(user):
    limit = Transaction.RISKY_LIMIT

    if user.is_manager():
        transactions = Transaction.objects.filter(is_approved=False, from_account__user__is_active=True).order_by('request_time') | Transaction.objects.filter(is_approved=False, to_account__user__is_active=True).order_by('request_time')

        transactions = transactions.filter(created_by__assigned_to=user) | transactions.filter(created_by__assigned_to__assigned_to=user, amount__gt=limit)

    elif user.is_admin():
        transactions = Transaction.objects.filter(is_approved=False).order_by('-amount', 'request_time')

    else:
        transactions = Transaction.objects.filter(is_approved=False, created_by__assigned_to=user, from_account__user__is_active=True).order_by('-amount', 'request_time') | \
                       Transaction.objects.filter(is_approved=False, created_by__assigned_to=user, to_account__user__is_active=True).order_by('-amount', 'request_time')

    links = []

    for transaction in transactions.distinct():
        link = reverse('app:TransactionView', kwargs={
            'transaction_id': transaction.id,
        })
        links += [
            (transaction.__str__(), link)
        ]

    return links


def get_pending_transaction_requests_of_user(user):
    # Transactions involving user accounts with debit/transfer or credit
    transactions = Transaction.objects.filter(is_approved=False, from_account__user=user, from_account__user__is_active=True) | Transaction.objects.filter(is_approved=False, to_account__user=user, to_account__user__is_active=True)

    transactions = transactions.order_by('-request_time')

    links = []

    for transaction in transactions:
        link = reverse('app:TransactionView', kwargs={
            'transaction_id': transaction.id,
        })
        links += [
            (transaction.__str__(), link)
        ]

    return links


def get_completed_transactions(user=None):
    transactions = Transaction.objects.filter(is_complete=True).order_by('-complete_time')

    if user:
        transactions = transactions.filter(from_account__user=user) | transactions.filter(to_account__user=user)

    links = []

    for transaction in transactions:
        link = reverse('app:TransactionView', kwargs={
            'transaction_id': transaction.id,
        })
        links += [
            (transaction.__str__(), link)
        ]

    return links


def get_pending_risky_transaction_of_user(user):
    limit = Transaction.RISKY_LIMIT
    transactions = []
    if user.is_manager():
        transactions = Transaction.objects.filter(is_approved=False, from_account__user__is_active=True).order_by('request_time') | Transaction.objects.filter(is_approved=False, to_account__user__is_active=True).order_by('request_time')
        transactions = transactions.filter(created_by__assigned_to=user, amount__gt=limit) | transactions.filter(created_by__assigned_to__assigned_to=user, amount__gt=limit)

    elif user.is_admin():
        transactions = Transaction.objects.filter(is_approved=False, from_account__user__is_active=True).order_by('request_time') | Transaction.objects.filter(is_approved=False, to_account__user__is_active=True).order_by('request_time')
        transactions = transactions.filter(amount__gt=limit)

    links = []
    for transaction in transactions:
        link = reverse('app:TransactionView', kwargs={
            'transaction_id': transaction.id,
        })
        links += [
            (transaction.__str__(), link)
        ]

    return links


@db_transaction.atomic
def delete_transaction(transaction):
    transaction = Transaction.objects.filter(id=transaction.id).select_for_update().first()

    if transaction is None or transaction.is_approved:
        return False

    transaction.delete()
    return True


def get_transaction(transaction_id):
    return Transaction.objects.filter(id=transaction_id).first()


def is_transaction_limit_reached(user):
    limit = 20

    if Transaction.objects.filter(created_by=user, is_approved=False).count() > limit:
        return True

    return False
