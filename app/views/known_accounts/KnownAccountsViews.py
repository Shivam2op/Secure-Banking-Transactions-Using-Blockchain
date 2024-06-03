from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from app.forms.KnownAccountsForms import KnownAccountsForm
from app.mixins import LoginAndOTPRequiredMixin
from app.models import MyUser
from app.views.known_accounts.KnownAccountHelpers import check_same_user_account, get_account_from_number, \
    check_duplicate, get_known_accounts
import logging

logger = logging.getLogger(__name__)


class EnterKnownAccountsView(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        user = request.user

        target_user = MyUser.objects.filter(id=user.id, user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT), is_active=True).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You cannot have known accounts',
            })

        form = KnownAccountsForm()

        return render(request, 'form_template.html', {
            'title': 'Known Accounts',
            'form': form,
        })

    def post(self, request):
        user = request.user

        target_user = MyUser.objects.filter(id=user.id, user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT), is_active=True).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You cannot have known accounts',
            })

        form = KnownAccountsForm(request.POST)

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

            instance = form.save(commit=False)
            instance.user = target_user
            instance.account = account
            instance.save()

            messages.success(request, 'Account Submitted')
            logger.info("New known account %s added by %s", account.__str__(), str(target_user.username))

            return HttpResponseRedirect(reverse('app:HomeView'))

        return render(request, 'form_template.html', {
            'title': 'Known Accounts',
            'form': form,
        })


class ViewKnownAccounts(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        user = request.user

        target_user = MyUser.objects.filter(id=user.id, user_type__in=(MyUser.INDIVIDUAL_USER, MyUser.MERCHANT), is_active=True).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You cannot have known accounts',
            })

        links = get_known_accounts(target_user.id)

        return render(request, 'display_list.html', {
            'title': 'Known Accounts',
            'links': links,
        })








