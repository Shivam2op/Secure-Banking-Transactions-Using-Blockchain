from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
#from django.utils.encoding import force_text
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic.base import View
from django_otp.plugins.otp_totp.models import TOTPDevice

from app.forms import SignUpForms
from app.mixins import LoginAndOTPRequiredMixin
from app.models import MyUser
from app.tokens import otp_token_generator
from app.views import CommonHelpers
from app.views.signup import SignUpHelpers
from django.db import transaction as db_transaction
import logging

logger = logging.getLogger(__name__)


class SignUp(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        if request.user.is_admin():
            personal_form = SignUpForms.PersonalInfo(request.user)

            return render(request, 'signup.html', {
                'form': personal_form,
            })
        else:
            return render(request, 'error.html', {
                'err': 'You are not admin. Go away.',
            })

    def post(self, request):
        if request.user.is_admin():
            personal_form = SignUpForms.PersonalInfo(request.user, request.POST)

            if personal_form.is_valid():
                print(personal_form.cleaned_data)

                user = personal_form.save()

                messages.success(request, 'User Created')
                logger.info("User %s created by admin %s", str(user.username), str(request.user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))

            return render(request, 'signup.html', {
                'form': personal_form,
            })
        else:
            return render(request, 'error.html', {
                'err': 'You are not admin. Go away.',
            })


class OTPImage(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        user_id = request.user.id

        if SignUpHelpers.is_otp_device_confirmed(user_id):
            logout(request)

            return render(request, 'error.html', {
                'err': 'Already Configured. You can not view this now.'
            })

        # Do this here so that qr code is visible first time
        device = SignUpHelpers.get_otp_device(user_id)
        device.confirmed = True
        device.save()

        # Show image if device not configured
        qr = SignUpHelpers.get_qrcode(user_id)

        return qr


# Unused
class OTPSetup(LoginRequiredMixin, View):

    def get(self, request):
        user_id = request.user.id
        device = SignUpHelpers.get_otp_device(user_id)

        return render(request, 'qrcode.html', {
            'device': device,
        })


class UserConfirmation(View):

    def get(self, request, uidb, token):
        INTERNAL_RESET_URL_TOKEN = 'set-otp'
        INTERNAL_RESET_SESSION_TOKEN = '_otp_reset_token'

        try:
            #uid = force_text(urlsafe_base64_decode(uidb))
            uid = force_str(urlsafe_base64_decode(uidb))
            user = MyUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
            user = None

        if user is not None:
            if token == INTERNAL_RESET_URL_TOKEN:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if otp_token_generator.check_token(user, session_token):
                    device = SignUpHelpers.get_otp_device(user.id)

                    user.is_active = True
                    user.save()

                    CommonHelpers.login_and_verify_without_otp(request, user, 'django.contrib.auth.backends.ModelBackend')

                    request.session['_otp_verified'] = True

                    return render(request, 'qrcode.html', {
                        'device': device,
                        'hide_navbar_function_buttons': True,
                    })
            else:
                if otp_token_generator.check_token(user, token):

                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(token, INTERNAL_RESET_URL_TOKEN)
                    return HttpResponseRedirect(redirect_url)

        return render(request, 'error.html', {
            'err': 'Invalid Link. You Hacker.'
        })


# Unused
class ChangePassword(PasswordChangeView):

    template_name = 'form_template.html'
    success_url = reverse_lazy('app:HomeView')


class PasswordResetConfirm(PasswordResetConfirmView):

    template_name = 'form_template.html'
    success_url = reverse_lazy('app:HomeView')

    def form_valid(self, form):
        user = form.save()
        logger.info("Password Reset Done for %s", str(user.username))

        CommonHelpers.send_confirmation_mail(user)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context['hide_navbar_function_buttons'] = True
        else:
            self.template_name = 'error.html'
            context = {
                'err': 'Invalid link. You hacker.',
            }

        return context


class PasswordResetRequestView(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_admin():
            form = SignUpForms.PasswordResetRequestForm()

            return render(request, 'form_template.html', {
                'title': 'Reset User',
                'form': form,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permission for this',
            })

    def post(self, request):

        user = request.user

        if user.is_admin():
            form = SignUpForms.PasswordResetRequestForm(request.POST)

            if form.is_valid():
                target_user = form.cleaned_data['user']

                with db_transaction.atomic():
                    target_user = MyUser.objects.filter(id=target_user.id).select_for_update().first()

                    if target_user:
                        target_user.is_active = False
                        target_user.save()

                        TOTPDevice.objects.filter(user=target_user).delete()
                        TOTPDevice.objects.create(name='Phone', user=target_user, confirmed=False)

                    else:
                        return render(request, 'error.html', {
                            'err': 'Action could not be completed',
                        })

                CommonHelpers.send_password_mail(target_user)

                messages.success(request, 'Request Initiated')
                logger.info("Password Reset Initiated for %s by admin %s", str(target_user.username), str(request.user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))

            return render(request, 'form_template.html', {
                'title': 'Reset User',
                'form': form,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permission for this',
            })
