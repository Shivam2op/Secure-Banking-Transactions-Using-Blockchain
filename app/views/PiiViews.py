from django.contrib import messages
from django.contrib.auth.models import update_last_login
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
#from django.utils.encoding import force_text
from django.utils.encoding import force_str
#django.utils.encoding.force_text = force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from guardian.shortcuts import remove_perm

from app.forms import TransactionForms
from app.forms.PiiForm import PiiForm
from app.forms.RequestForms import RequestForm
from app.mixins import LoginAndOTPRequiredMixin
from app.models import PII, MyUser, UserRequest
from app.tokens import PIITokenGenerator
from app.views import CommonHelpers
from app.views.users import UserHelpers
import logging

logger = logging.getLogger(__name__)

class PiiView(LoginAndOTPRequiredMixin, View):

    def get(self, request, user_id):
        user = request.user

        target_user = MyUser.objects.filter(id=user_id, is_active=True).filter(user_type=MyUser.INDIVIDUAL_USER).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

        value = PII.objects.filter(user=target_user).first()

        if CommonHelpers.is_int_equal(user_id, user.id):
            if value:
                form = TransactionForms.VerifyOTPForm()

                return render(request, 'form_template.html', {
                    'title': 'Confirm OTP',
                    'form': form,
                    'form_virtual_keyboard': True,
                })

            else:
                form = PiiForm()
                return render(request, 'form_template.html', {
                    'title': 'PII',
                    'form': form,
                })

        elif user.has_perm('read_pii', value):
            remove_perm('read_pii', user, value)

            # Update login time to invalidate link
            update_last_login(None, user)

            if value:
                form = PiiForm(instance=value)
                return render(request, 'form_template.html', {
                    'title': 'PII',
                    'form': form,
                    'readonly': True,
                    'hide_btn': True,
                })
            else:
                return render(request, 'error.html', {
                    'err': 'User has not entered PII.',
                })

        elif user.is_admin():
            if value:
                form = RequestForm(initial={
                    'to_user': 'Government',
                    'request_type': UserRequest.READ,
                    'model_type': UserRequest.PII_ACCESS,
                    'for_url': request.build_absolute_uri(),
                })

                return render(request, 'form_template.html', {
                    'title': 'Request For Access',
                    'form': form,
                    'readonly': True,
                })

            else:
                return render(request, 'error.html', {
                    'err': 'User has not entered PII.',
                })

        return render(request, 'error.html', {
            'err': 'You do not have permissions to view this',
        })

    def post(self, request, user_id):

        user = request.user

        target_user = MyUser.objects.filter(id=user_id, is_active=True).filter(user_type=MyUser.INDIVIDUAL_USER).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

        value = PII.objects.filter(user=target_user).first()

        if CommonHelpers.is_int_equal(user_id, user.id):
            if value:
                form = TransactionForms.VerifyOTPForm(request, data=request.POST)

                if form.is_valid():
                    form = PiiForm(instance=value)
                    return render(request, 'form_template.html', {
                        'title': 'PII',
                        'form': form,
                        'readonly': True,
                        'hide_btn': True,
                    })

                messages.error(request, 'Incorrect OTP')
                return HttpResponseRedirect(reverse('app:HomeView'))

            else:
                form = PiiForm(data=request.POST)

                if form.is_valid():
                    instance = form.save(commit=False)
                    instance.user = user
                    instance.save()
                    messages.success(request, 'PII Submitted')

                    logger.info("PII added by %s", str(target_user.username))

                    return HttpResponseRedirect(reverse('app:HomeView'))

                return render(request, 'form_template.html', {
                    'title': 'PII',
                    'form': form,
                })

        elif user.is_admin():
            if value:
                CommonHelpers.send_pii_request_mail(user, target_user, value)

                messages.success(request, 'Request Sent To Government')

                logger.info("PII request for %s sent by %s", str(target_user.username), str(user.username))


                return HttpResponseRedirect(reverse('app:HomeView'))

            else:
                return render(request, 'error.html', {
                    'err': 'User has not entered PII.',
                })

        return render(request, 'error.html', {
            'err': 'You do not have permissions to view this',
        })


class GovtPIIAccess(View):
    def get(self, request, uidb1, uidb2, token):
        INTERNAL_RESET_URL_TOKEN = 'approve-request'
        INTERNAL_RESET_SESSION_TOKEN = '_approve_request_token'

        try:
            uid = force_text(urlsafe_base64_decode(uidb1))
            from_user = MyUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
            from_user = None

        try:
            uid = force_text(urlsafe_base64_decode(uidb2))
            target_user = MyUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
            target_user = None

        if from_user is not None and target_user is not None:
            pii_obj = PII.objects.filter(user=target_user).first()

            pii_token_generator = PIITokenGenerator(pii_obj)
            url = reverse('app:Pii', kwargs={
                'user_id': target_user.id,
            })

            if token == INTERNAL_RESET_URL_TOKEN:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)

                if pii_token_generator.check_token(from_user, session_token):

                    if pii_obj:
                        form = RequestForm(initial={
                            'to_user': from_user,
                            'request_type': UserRequest.READ,
                            'model_type': UserRequest.PII_ACCESS,
                            'for_url': request.build_absolute_uri(url),
                        })

                        return render(request, 'form_template.html', {
                            'title': 'Approve Request',
                            'form': form,
                            'hide_navbar_function_buttons': True,
                            'readonly': True,
                        })

                    else:
                        return render(request, 'error.html', {
                            'err': 'User has not entered PII.',
                        })

            else:
                if pii_token_generator.check_token(from_user, token):

                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(token, INTERNAL_RESET_URL_TOKEN)
                    return HttpResponseRedirect(redirect_url)

        return render(request, 'error.html', {
            'err': 'Invalid Link. You Hacker.'
        })

    def post(self, request, uidb1, uidb2, token):
        INTERNAL_RESET_URL_TOKEN = 'approve-request'
        INTERNAL_RESET_SESSION_TOKEN = '_approve_request_token'

        try:
            uid = force_text(urlsafe_base64_decode(uidb1))
            from_user = MyUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
            from_user = None

        try:
            uid = force_text(urlsafe_base64_decode(uidb2))
            target_user = MyUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
            target_user = None

        if from_user is not None and target_user is not None:
            pii_obj = PII.objects.filter(user=target_user).first()

            pii_token_generator = PIITokenGenerator(pii_obj)

            if token == INTERNAL_RESET_URL_TOKEN:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)

                if pii_token_generator.check_token(from_user, session_token):

                    if pii_obj:
                        user_request = UserRequest(
                            from_user=from_user,
                            request_type=UserRequest.READ,
                            model_type=UserRequest.PII_ACCESS,
                            pii_obj=pii_obj,
                        )
                        if UserHelpers.assign_permissions(user_request):

                            CommonHelpers.send_request_approval_mail(user_request)
                            messages.success(request, 'Request Approved')
                            logger.info("PII request of %s approved by Government for %s", str(user_request.from_user),str(target_user.username))

                            return HttpResponseRedirect(reverse('app:HomeView'))

                        else:
                            return render(request, 'error.html', {
                                'err': 'Action could not be completed',
                            })
                    else:
                        return render(request, 'error.html', {
                            'err': 'User has not entered PII.',
                        })

            else:
                if pii_token_generator.check_token(from_user, token):

                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(token, INTERNAL_RESET_URL_TOKEN)
                    return HttpResponseRedirect(redirect_url)

        return render(request, 'error.html', {
            'err': 'Invalid Link. You Hacker.'
        })


class ViewPii(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        user = request.user
        if user.is_admin():
            links = CommonHelpers.get_pii_link()

            return render(request, 'list_template.html', {
                'title': 'All Users with PII',
                'links': links,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })
