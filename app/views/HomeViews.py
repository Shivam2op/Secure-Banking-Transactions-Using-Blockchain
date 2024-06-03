from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.base import View
from app.mixins import LoginAndOTPRequiredMixin
from app.views import CommonHelpers


class HomeView(View):

    def get(self, request):

        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('app:DashboardView'))

        return render(request, 'home.html', {
            'home': True,
        })


class DashboardView(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        links = []
        balance = None

        if user.is_admin():
            template = 'dashboard.html'
            title = 'Admin'
            links = CommonHelpers.get_admin_links()
        elif user.is_manager():
            template = 'dashboard.html'
            title = 'Manager'
            links = CommonHelpers.get_manager_links()
        elif user.is_employee():
            template = 'dashboard.html'
            title = 'Employee'
            links = CommonHelpers.get_employee_links()
        elif user.is_merchant():
            template = 'dashboard.html'
            title = 'Merchant'
            links = CommonHelpers.get_merchant_links(user.id)
            balance = CommonHelpers.get_user_total_balance(user.id)
        elif user.is_individual_user():
            template = 'dashboard.html'
            title = 'Individual User'
            links = CommonHelpers.get_individual_user_links(user.id)
            balance = CommonHelpers.get_user_total_balance(user.id)
        else:
            template = 'error.html'
            title = ''

        return render(request, template, {
            'title': title,
            'links': links,
            'balance': balance,
        })
