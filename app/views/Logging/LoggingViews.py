from django.shortcuts import render
from django.views import View

from app.mixins import LoginAndOTPRequiredMixin
from app.models import MyUser
from app.views.Logging.LoggingHelpers import get_system_log, get_transaction_log, get_system_files, \
    get_transaction_files


class SystemLogsView(LoginAndOTPRequiredMixin, View):
    def get(self, request):
        user = request.user

        if user.is_admin():

            links = get_system_files()

            return render(request, 'list_template.html', {
                'title': 'System Logs',
                'links': links,
            })

        return render(request, 'error.html', {
            'err': 'You do not have permissions for this',
        })


class SystemLogsDate(LoginAndOTPRequiredMixin, View):
    def get(self, request, log_id):
        user = request.user

        if user.is_admin():

            links = get_system_log(log_id)

            if links:

                return render(request, 'display_list.html', {
                    'title': 'System Logs',
                    'links': links,
                })

            return render(request, 'error.html', {
                'err': "File is empty or does not exist"
            })

        return render(request, 'error.html', {
            'err': 'You do not have permissions for this',
        })


class TransactionLogsView(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        user = request.user

        if user.is_admin():

            links = get_transaction_files()

            return render(request, 'list_template.html', {
                'title': 'Transaction Logs',
                'links': links,
            })

        return render(request, 'error.html', {
            'err': 'You do not have permissions for this',
        })


class TransactionLogsDate(LoginAndOTPRequiredMixin, View):
    def get(self, request, log_id):
        user = request.user

        if user.is_admin():

            links = get_transaction_log(log_id)

            if links:

                return render(request, 'display_list.html', {
                    'title': 'Transaction Logs',
                    'links': links,
                })

            return render(request, 'error.html', {
                'err': "File is empty or does not exist"
            })

        return render(request, 'error.html', {
            'err': 'You do not have permissions for this',
        })
