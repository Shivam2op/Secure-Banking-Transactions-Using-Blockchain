from django.views import View
from django_su.views import su_login, su_logout, login_as_user

from app.forms.SuForms import MyUserSuForm
from app.mixins import LoginAndOTPRequiredMixin


class CustomSuLogin(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        return su_login(request, template_name='form_template.html', form_class=MyUserSuForm)

    def post(self, request):
        return su_login(request, template_name='form_template.html', form_class=MyUserSuForm)


class CustomSuLogout(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        return su_logout(request)


class CustomSuLoginAsUser(LoginAndOTPRequiredMixin, View):

    def post(self, request, user_id):
        return login_as_user(request, user_id)
