from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from app.forms.AccountForms import UserAccountForm
from app.forms.RequestForms import CreateRequestForm
from app.mixins import LoginAndOTPRequiredMixin
from app.models import UserRequest
from app.views import CommonHelpers
from app.views.accounts import AccountHelpers
import logging

logger = logging.getLogger(__name__)

class UserAccountsView(LoginAndOTPRequiredMixin, View):

    def get(self, request, user_id):

        user = request.user
        if CommonHelpers.is_int_equal(user_id, user.id) or user.is_admin():

            if not AccountHelpers.is_user_having_account(user_id):
                return render(request, 'error.html', {
                    'err': 'User has no accounts',
                })

            links = AccountHelpers.get_user_accounts(user_id)

            return render(request, 'list_template.html', {
                'title': 'User Accounts',
                'links': links,
            })

        elif user.is_employee() or user.is_manager():
            if not AccountHelpers.is_user_having_account(user_id):
                return render(request, 'error.html', {
                    'err': 'User has no accounts',
                })

            links = AccountHelpers.get_user_assigned_accounts(user_id,user)

            return render(request, 'list_template.html', {
                'title': 'User Accounts',
                'links': links,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this.',
            })


class AccountView(LoginAndOTPRequiredMixin, View):

    def get(self, request, user_id, account_id):

        user = request.user

        if CommonHelpers.is_int_equal(user_id, user.id) or user.is_admin():
            account = AccountHelpers.get_account(user_id, account_id)

            if account:
                form = UserAccountForm(instance=account)

                return render(request, 'form_template.html', {
                    'title': 'Account',
                    'form': form,
                    'hide_btn': True,
                    'readonly': True,
                })

            else:
                return render(request, 'error.html', {
                    'err': 'Account does not exist.',
                })

        elif user.is_employee() or user.is_manager():
            account = AccountHelpers.get_assigned_account_details(user_id, account_id,user)

            if account:
                form = UserAccountForm(instance=account)

                return render(request, 'form_template.html', {
                    'title': 'Account',
                    'form': form,
                    'hide_btn': True,
                    'readonly': True,
                })

            else:
                return render(request, 'error.html', {
                    'err': 'Account does not exist or You do not have permissions to access it.',
                })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this.',
            })


class UsersHavingAccountView(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_admin():
            links = AccountHelpers.get_users_having_accounts()

            return render(request, 'list_template.html', {
                'title': 'Users Having Accounts',
                'links': links,
            })

        elif user.is_employee() or user.is_manager():
            links = AccountHelpers.get_users_assigned_to_manager_employee(user)
            return render(request, 'list_template.html', {
                'title': 'Users Having Accounts',
                'links': links,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this.',
            })


class UserAddAccountView(LoginAndOTPRequiredMixin, View):

    def get(self, request, user_id):

        user = request.user

        if CommonHelpers.is_int_equal(user.id, user_id) and not user.is_internal_user():

            form = CreateRequestForm(initial={
                'request_type': UserRequest.CREATE,
                'model_type': UserRequest.ACCOUNT,
            })

            return render(request, 'form_template.html', {
                'title': 'Add Account',
                'form': form,
                'readonly': True,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

    def post(self, request, user_id):

        user = request.user

        if CommonHelpers.is_int_equal(user.id, user_id) and not user.is_internal_user():

            form = CreateRequestForm(data={
                'request_type': UserRequest.CREATE,
                'model_type': UserRequest.ACCOUNT,
            })

            if form.is_valid():

                user_request = form.save(commit=False)
                user_request.from_user = user
                user_request.to_user = user.assigned_to

                if CommonHelpers.is_request_duplicate(user_request):
                    messages.warning(request, 'Request Already Sent')

                    return HttpResponseRedirect(reverse('app:HomeView'))

                user_request.save()

                messages.success(request, 'Request Sent To %s' % user_request.to_user)
                logger.info("Request for new account sent by %s", str(user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))

            return render(request, 'form_template.html', {
                'title': 'Add Account',
                'form': form,
                'readonly': True,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })
