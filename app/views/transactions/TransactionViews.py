from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from guardian.shortcuts import remove_perm

from app.forms import TransactionForms
from app.forms.RequestForms import RequestForm
from app.forms.TransactionForms import TransactionLocatorForm
from app.mixins import LoginAndOTPRequiredMixin
from app.models import Transaction, UserRequest, MyUser
from app.views import CommonHelpers
from app.views.PKI import PKIHelpers
from app.views.accounts import AccountHelpers
from app.views.transactions import TransactionHelpers
from django.db import transaction as db_transaction
import logging

logger = logging.getLogger(__name__)


class TransactionRequest(LoginAndOTPRequiredMixin, View):
    INTERNAL_PKI_TOKEN = '_server_encrypted_data'

    def get(self, request):
        user = request.user
        if TransactionHelpers.is_transaction_limit_reached(user):
            return render(request, 'error.html', {
                'err': 'You cannot create more transactions due to pending transactions'
            })

        # PKI
        user_encrypted_data, server_encrypted_data = PKIHelpers.get_encrypted_token(user)

        if user_encrypted_data is None or server_encrypted_data is None:
            return render(request, 'error.html', {
                'err': 'PKI has not been configured. Set it up to perform transactions.',
            })

        request.session[self.INTERNAL_PKI_TOKEN] = server_encrypted_data
        use_pki = PKIHelpers.get_pki_dictionary(user_encrypted_data)

        if user.is_employee():
            form = TransactionForms.InternalRequestForm(user)
        elif user.is_internal_user():
            return render(request, 'error.html', {
                'err': 'You cannot create transactions'
            })
        elif AccountHelpers.is_user_having_account(user.id):
            form = TransactionForms.ExternalRequestForm(user)
        else:
            return render(request, 'error.html', {
                'err': 'User has no accounts.'
            })

        return render(request, 'form_template.html', {
            'title': 'Transaction',
            'form': form,
            'use_pki': use_pki,
        })

    def post(self, request):
        user = request.user

        if TransactionHelpers.is_transaction_limit_reached(user):
            return render(request, 'error.html', {
                'err': 'You cannot create more transactions due to pending transactions'
            })

        if user.is_employee():
            form = TransactionForms.InternalRequestForm(user, request.POST)
        elif user.is_internal_user():
            return render(request, 'error.html', {
                'err': 'You cannot create transactions'
            })
        elif AccountHelpers.is_user_having_account(user.id):
            form = TransactionForms.ExternalRequestForm(user, request.POST)
        else:
            return render(request, 'error.html', {
                'err': 'User has no accounts.'
            })

        if form.is_valid():
            # PKI Verify
            pki_token = request.POST.get('pki_token', None)
            internal_pki_token = request.session.get(self.INTERNAL_PKI_TOKEN, None)

            if pki_token is None or internal_pki_token is None:
                return render(request, 'error.html', {
                    'err': 'PKI Verification Failed. Try to reset your PKI and try again.'
                })

            if PKIHelpers.verify_pki(pki_token, internal_pki_token):
                print('PKI Verified')
            else:
                return render(request, 'error.html', {
                    'err': 'PKI Verification Failed. Try to reset your PKI and try again.'
                })

            otp_token = request.POST.get('otp_token', None)

            if not otp_token:

                extra_form = TransactionForms.VerifyOTPForm()

                return render(request, 'form_template.html', {
                    'title': 'Confirm OTP',
                    'form': form,
                    'extra_form': extra_form,
                    'extra_form_virtual_keyboard': True,
                })

            extra_form = TransactionForms.VerifyOTPForm(request, data=request.POST)

            if extra_form.is_valid():
                transaction = form.save(commit=False)
                transaction.created_by = user
                transaction.save()

                messages.success(request, 'Transaction Created')
                logger.info("Request for transaction created by %s", str(user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))

            else:
                messages.error(request, 'Incorrect OTP')

                return HttpResponseRedirect(reverse('app:HomeView'))

        return render(request, 'form_template.html', {
            'form': form,
            'title': 'Transaction',
        })


class TransactionView(LoginAndOTPRequiredMixin, View):
    INTERNAL_PKI_TOKEN = '_server_encrypted_data'

    def get(self, request, transaction_id):
        user = request.user

        transaction = TransactionHelpers.get_transaction(transaction_id)

        if user.is_internal_user():

            if transaction:
                form = TransactionForms.InternalRequestForm(user=user, instance=transaction)

                # Not already approved
                if not transaction.is_approved:

                    # PKI
                    user_encrypted_data, server_encrypted_data = PKIHelpers.get_encrypted_token(user)

                    if user_encrypted_data is None or server_encrypted_data is None:
                        return render(request, 'error.html', {
                            'err': 'PKI has not been configured. Set it up to perform transactions.',
                        })

                    request.session[self.INTERNAL_PKI_TOKEN] = server_encrypted_data
                    use_pki = PKIHelpers.get_pki_dictionary(user_encrypted_data)

                    extra_form = TransactionForms.VerifyOTPForm()

                    if transaction.is_risky():
                        if transaction.created_by.get_assigned_manager() == user or user.is_admin():
                            return render(request, 'form_template.html', {
                                'title': 'Approve Transaction',
                                'form': form,
                                'readonly': True,
                                'btn_title': 'Approve',
                                'extra_btn_title': 'Decline',
                                'use_pki': use_pki,
                                'extra_form': extra_form,
                                'extra_form_virtual_keyboard': True,
                                'extra_form_readonly': False,
                            })

                    elif transaction.created_by.assigned_to == user or user.is_admin():
                        return render(request, 'form_template.html', {
                            'title': 'Approve Transaction',
                            'form': form,
                            'readonly': True,
                            'btn_title': 'Approve',
                            'extra_btn_title': 'Decline',
                            'use_pki': use_pki,
                            'extra_form': extra_form,
                            'extra_form_virtual_keyboard': True,
                            'extra_form_readonly': False,
                        })

                    elif transaction.created_by.get_assigned_manager() == user and user.has_perm('read_transaction', transaction):
                        return render(request, 'form_template.html', {
                            'title': 'Approve Transaction',
                            'form': form,
                            'readonly': True,
                            'btn_title': 'Approve',
                            'extra_btn_title': 'Decline',
                            'use_pki': use_pki,
                            'extra_form': extra_form,
                            'extra_form_virtual_keyboard': True,
                            'extra_form_readonly': False,
                        })

                    elif transaction.created_by == user:
                        return render(request, 'form_template.html', {
                            'title': 'Transaction',
                            'form': form,
                            'readonly': True,
                            'hide_btn': True,
                        })

                    elif transaction.created_by.get_assigned_manager() == user:
                        send_request_to = transaction.created_by

                        form = RequestForm(initial={
                            'to_user': send_request_to,
                            'request_type': UserRequest.READ,
                            'model_type': UserRequest.TRANSACTION,
                            'for_url': request.build_absolute_uri(),
                        })

                        return render(request, 'form_template.html', {
                            'title': 'Request For Access',
                            'form': form,
                            'readonly': True,
                            'extra_btn_title': 'Request Admin',
                        })

                    return render(request, 'error.html', {
                        'err': 'You do not have permissions to view or approve this transaction.'
                    })

                else:

                    if user.is_admin():
                        return render(request, 'form_template.html', {
                            'title': 'Transaction',
                            'form': form,
                            'hide_btn': True,
                            'readonly': True,
                        })

                    elif transaction.created_by == user or transaction.approved_by == user:
                        return render(request, 'form_template.html', {
                            'title': 'Transaction',
                            'form': form,
                            'hide_btn': True,
                            'readonly': True,
                        })

                    elif user.has_perm('read_transaction', transaction):
                        remove_perm('read_transaction', user, transaction)

                        return render(request, 'form_template.html', {
                            'title': 'Transaction',
                            'form': form,
                            'readonly': True,
                            'hide_btn': True,
                        })

                    else:
                        send_request_to = transaction.created_by

                        form = RequestForm(initial={
                            'to_user': send_request_to,
                            'request_type': UserRequest.READ,
                            'model_type': UserRequest.TRANSACTION,
                            'for_url': request.build_absolute_uri(),
                        })

                        return render(request, 'form_template.html', {
                            'title': 'Request For Access',
                            'form': form,
                            'readonly': True,
                            'extra_btn_title': 'Request Admin',
                        })

        else:

            if transaction:
                from_user_id = -1
                to_user_id = -1

                if transaction.from_account:
                    from_user = transaction.from_account.user
                    from_user_id = from_user.id

                if transaction.to_account:
                    to_user = transaction.to_account.user
                    to_user_id = to_user.id

                if CommonHelpers.is_int_equal(user.id, from_user_id) or CommonHelpers.is_int_equal(user.id, to_user_id):

                    form = TransactionForms.ExternalRequestForm(user=user, instance=transaction)

                    return render(request, 'form_template.html', {
                        'title': 'Transaction',
                        'form': form,
                        'hide_btn': True,
                        'readonly': True,
                    })

                return render(request, 'error.html', {
                    'err': 'You do not have permission to view this.',
                })

        # Does not exist
        return render(request, 'error.html', {
            'err': 'Transaction does not exist.',
        })

    def post(self, request, transaction_id):
        user = request.user

        if user.is_internal_user():
            transaction = Transaction.objects.filter(id=transaction_id, is_approved=False).select_for_update().first()

            if 'Approve' in request.POST:
                approve_transaction = True
            elif 'Decline' in request.POST:
                approve_transaction = False

            else:
                transaction = Transaction.objects.filter(id=transaction_id).first()

                if transaction is None:
                    return render(request, 'error.html', {
                        'err': 'Transaction does not exist.',
                    })

                request_admin = False
                if 'Request Admin' in request.POST:
                    request_admin = True

                send_request_to = transaction.created_by
                if request_admin and not user.is_admin():
                    send_request_to = user.get_assigned_admin()

                form = RequestForm(data={
                    'to_user': send_request_to.id,
                    'request_type': UserRequest.READ,
                    'model_type': UserRequest.TRANSACTION,
                    'for_url': request.build_absolute_uri(),
                })

                if form.is_valid():
                    user_request = form.save(commit=False)
                    user_request.from_user = user
                    user_request.transaction_obj = transaction

                    if CommonHelpers.is_request_duplicate(user_request):
                        messages.warning(request, 'Request Already Sent')

                        return HttpResponseRedirect(reverse('app:HomeView'))

                    user_request.save()

                    messages.success(request, 'Request Sent To %s' % user_request.to_user)
                    logger.info("Request to view transaction created by %s", str(user.username))

                    return HttpResponseRedirect(reverse('app:HomeView'))

                return render(request, 'form_template.html', {
                    'title': 'Request For Access',
                    'form': form,
                    'readonly': True,
                    'extra_btn_title': 'Request Admin',
                })

            if transaction is None:
                return render(request, 'error.html', {
                    'err': 'Transaction already resolved.'
                })

            verified_to_transact = False
            if transaction.is_risky():
                if transaction.created_by.get_assigned_manager() == user or user.is_admin():
                    verified_to_transact = True

            else:
                if transaction.created_by.assigned_to == user or user.is_admin():
                    verified_to_transact = True
                elif transaction.created_by.get_assigned_manager() == user and user.has_perm('read_transaction', transaction):
                    remove_perm('read_transaction', user, transaction)
                    verified_to_transact = True

            if verified_to_transact:
                # PKI Verify
                pki_token = request.POST.get('pki_token', None)
                internal_pki_token = request.session.get(self.INTERNAL_PKI_TOKEN, None)

                if pki_token is None or internal_pki_token is None:
                    return render(request, 'error.html', {
                        'err': 'PKI Verification Failed. Try to reset your PKI and try again.'
                    })

                if PKIHelpers.verify_pki(pki_token, internal_pki_token):
                    print('PKI Verified')
                else:
                    return render(request, 'error.html', {
                        'err': 'PKI Verification Failed. Try to reset your PKI and try again.'
                    })

                extra_form = TransactionForms.VerifyOTPForm(request, data=request.POST)

                if extra_form.is_valid():
                    pass
                else:
                    messages.error(request, 'Incorrect OTP')
                    return HttpResponseRedirect(reverse('app:TransactionPending'))

                if approve_transaction:
                    # Perform Transaction
                    if TransactionHelpers.perform_transaction(transaction):

                        with db_transaction.atomic():
                            transaction = Transaction.objects.filter(id=transaction.id, is_approved=False).select_for_update().first()

                            if transaction:
                                transaction.approve(user)
                                transaction.complete()

                            else:
                                return render(request, 'error.html', {
                                    'err': 'Action could not be completed',
                                })

                        # Remove view permissions from manager when not approved by them
                        if transaction.created_by.get_assigned_manager().has_perm('read_transaction', transaction):
                            remove_perm('read_transaction', transaction.created_by.get_assigned_manager(), transaction)

                        CommonHelpers.send_transaction_complete_mail(transaction)

                        messages.success(request, 'Transaction Approved')

                        logger.info("Transaction %s from %s to %s for amount %s approved by %s", str(transaction.id), str(transaction.from_account), str(transaction.to_account), str(transaction.amount), str(user.username))

                        return HttpResponseRedirect(reverse('app:TransactionPending'))

                    else:
                        return render(request, 'error.html', {
                            'err': 'This transaction cannot be completed because of low balance or is already completed.',
                        })

                else:
                    # Decline Transaction
                    if not transaction.is_approved:
                        if TransactionHelpers.delete_transaction(transaction):

                            CommonHelpers.send_transaction_declined_mail(transaction)

                            messages.success(request, 'Transaction Declined')

                            logger.info("Transaction %s declined by : %s", str(transaction.id), str(user.username))

                            return HttpResponseRedirect(reverse('app:TransactionPending'))

                    return render(request, 'error.html', {
                        'err': 'Transaction cannot be declined because it is already approved.',
                    })

        return render(request, 'error.html', {
            'err': 'You do not have permission for this.',
        })


class TransactionPending(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_internal_user():
            links = TransactionHelpers.get_pending_transactions_assigned_to_user(user)

            return render(request, 'list_template.html', {
                'title': 'Pending Transactions',
                'links': links,
            })
        else:
            links = TransactionHelpers.get_pending_transaction_requests_of_user(user)

            return render(request, 'list_template.html', {
                'title': 'Pending Transactions',
                'links': links,
            })


class TransactionCompleted(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_internal_user():
            links = TransactionHelpers.get_completed_transactions()

            return render(request, 'list_template.html', {
                'title': 'Transaction History',
                'links': links,
            })
        elif AccountHelpers.is_user_having_account(user.id):
            links = TransactionHelpers.get_completed_transactions(user)

            return render(request, 'list_template.html', {
                'title': 'Transaction History',
                'links': links,
            })
        else:
            return render(request, 'error.html', {
                'err': 'You do not have permission to view this',
            })


class TransactionLocator(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_internal_user():
            queryset = Transaction.objects.filter(is_complete=True) | Transaction.objects.filter(is_complete=False, from_account__user__is_active=True) | Transaction.objects.filter(is_complete=False, to_account__user__is_active=True)

        elif user.is_individual_user():
            queryset = Transaction.objects.filter(from_account__user=user, from_account__user__is_active=True, is_complete=False) | Transaction.objects.filter(to_account__user=user, to_account__user__is_active=True, is_complete=False) | \
                       Transaction.objects.filter(from_account__user=user, is_complete=True) | Transaction.objects.filter(to_account__user=user, is_complete=True)

        elif user.is_merchant():
            queryset = Transaction.objects.filter(from_account__user=user, from_account__user__is_active=True, is_complete=False) | Transaction.objects.filter(from_account__user=user, is_complete=True) | \
                       Transaction.objects.filter(to_account__user=user, to_account__user__is_active=True, is_complete=False) | Transaction.objects.filter(to_account__user=user, is_complete=True) |\
                       Transaction.objects.filter(from_account__payment_account__merchant_user=user, from_account__payment_account__merchant_user__is_active=True, is_complete=False) | Transaction.objects.filter(from_account__payment_account__merchant_user=user, is_complete=True) | \
                       Transaction.objects.filter(to_account__payment_account__merchant_user=user, to_account__payment_account__merchant_user__is_active=True, is_complete=False) | Transaction.objects.filter(to_account__payment_account__merchant_user=user, is_complete=True)

        else:
            return render(request, 'error.html', {
                'err': 'This is sad.'
            })

        filter = TransactionLocatorForm(request.GET, queryset=queryset.distinct(), request=request)

        return render(request, 'filter_template.html', {
            'filter': filter,
            'form': filter.form,
            'title': 'Transaction Locator',
            'get': 'get',
            'btn_title': 'Search',
        })


class TransactionRisky(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        user = request.user

        if user.is_manager() or user.is_admin():
            links = TransactionHelpers.get_pending_risky_transaction_of_user(user)

            return render(request, 'list_template.html', {
                'title': 'Pending Risky Transactions',
                'links': links,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })


