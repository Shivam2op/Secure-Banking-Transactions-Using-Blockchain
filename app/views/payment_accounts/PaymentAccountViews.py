from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from app.forms.RequestForms import CreateRequestForm
from app.forms.PaymentAccountsForms import PaymentAccountsForm, RemovePaymentAccountForm
from app.mixins import LoginAndOTPRequiredMixin
from app.models import MyUser, UserRequest
from app.views import CommonHelpers
from app.views.known_accounts.KnownAccountHelpers import get_account_from_number, check_same_user_account
from app.views.payment_accounts.PaymentAccountHelpers import get_payment_accounts, check_duplicate
import logging

logger = logging.getLogger(__name__)


class EnterPaymentAccountsView(LoginAndOTPRequiredMixin, View):
    def get(self, request):
        user = request.user

        target_user = MyUser.objects.filter(id=user.id, user_type=MyUser.MERCHANT, is_active=True).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You cannot add user accounts',
            })

        form = PaymentAccountsForm()

        return render(request, 'form_template.html', {
            'title': 'User Accounts',
            'form': form,
        })

    def post(self, request):
        user = request.user

        target_user = MyUser.objects.filter(id=user.id, user_type=MyUser.MERCHANT, is_active=True).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, "error.html", {
                'err': "You cannot add client accounts"
            })

        form = PaymentAccountsForm(request.POST)

        if form.is_valid():
            acc_number = form.cleaned_data['account_number']
            account = get_account_from_number(acc_number)

            if check_same_user_account(target_user.id, acc_number):
                return render(request, 'error.html', {
                    'err': 'Please don\'t enter your own accounts.',
                })

            if check_duplicate(target_user.id, acc_number):
                return render(request, 'error.html', {
                    'err': 'Account exists in your list',
                })

            form = CreateRequestForm(data={
                'request_type': UserRequest.CREATE,
                'model_type': UserRequest.ACCOUNT,
            })

            if form.is_valid():

                user_request = form.save(commit=False)
                user_request.from_user = target_user
                user_request.to_user = account.user
                user_request.account_obj = account

                if CommonHelpers.is_request_duplicate(user_request):
                    messages.warning(request, 'Request Already Sent')

                    return HttpResponseRedirect(reverse('app:HomeView'))

                user_request.save()

                messages.success(request, 'Request Sent To %s' % user_request.to_user)
                logger.info("Request for new adding client account %s sent by %s", str(account.user.username), str(target_user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))
            else:

                return render(request, "error.html", {
                    'err': "Request could not be sent"
                })

        return render(request, 'form_template.html', {
            'title': 'User Accounts',
            'form': form,
        })

class ViewPaymentccounts(LoginAndOTPRequiredMixin, View):
    def get(self, request):
        user = request.user

        target_user = MyUser.objects.filter(id=user.id, user_type= MyUser.MERCHANT, is_active=True).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You cannot add user accounts',
            })

        links = get_payment_accounts(target_user.id)

        return render(request, 'display_list.html', {
            'title': 'Payment Accounts',
            'links': links,
        })

class RemovePaymentAccounts(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_merchant() or user.is_individual_user():

            form = RemovePaymentAccountForm(user)

            return render(request, 'form_template.html', {
                'title': 'Remove Merchant User Account Permission',
                'form': form,
            })

        return render(request, 'error.html', {
            'err': 'You do not have permissions to view this.',
        })

    def post(self, request):

        user = request.user

        if user.is_merchant() or user.is_individual_user():

            form = RemovePaymentAccountForm(user, request.POST)

            if form.is_valid():

                merchant_account = form.cleaned_data['merchant_account']
                merchant_account.delete()

                messages.success(request, 'Merchant permissions removed')
                logger.info("User account permissions of %s removed by %s", merchant_account.merchant_user.__str__(), str(user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))

        return render(request, 'error.html', {
            'err': 'You do not have permissions to view this.',
        })
