from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from guardian.shortcuts import remove_perm

from app.forms.RequestForms import RequestForm
from app.forms.TransactionForms import VerifyOTPForm
from app.forms.UserForms import UserProfileForm, EditUserProfileForm, UserDeleteForm
from app.mixins import LoginAndOTPRequiredMixin
from app.models import MyUser, UserRequest
from app.views import CommonHelpers
from app.views.users import UserHelpers
import logging

logger = logging.getLogger(__name__)


class AllUsersView(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_admin():
            links = UserHelpers.get_users(True)

            return render(request, 'list_template.html', {
                'title': 'All Users',
                'links': links,
            })

        elif user.is_internal_user():
            links = UserHelpers.get_users()

            return render(request, 'list_template.html', {
                'title': 'All Users',
                'links': links,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })


class UserProfile(LoginAndOTPRequiredMixin, View):

    def get(self, request, user_id):

        user = request.user
        target_user = MyUser.objects.filter(id=user_id, is_active=True).exclude(username=MyUser.ANON).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

        edit_link = ('Edit', reverse('app:UserProfileEdit', kwargs={
            'user_id': target_user.id,
        }))

        if CommonHelpers.is_int_equal(user_id, user.id) or user.is_admin() and not target_user.is_admin():
            form = UserProfileForm(instance=target_user, user_id=user_id)

            return render(request, 'form_template.html', {
                'title': 'User Profile',
                'form': form,
                'hide_btn': True,
                'readonly': True,
                'link': edit_link,
            })

        elif user.has_perm('read_user', target_user) or user.has_perm('edit_user', target_user):
            remove_perm('read_user', user, target_user)
            form = UserProfileForm(instance=target_user, user_id=user_id)

            return render(request, 'form_template.html', {
                'title': 'User Profile',
                'form': form,
                'hide_btn': True,
                'readonly': True,
                'link': edit_link,
            })

        elif user.is_internal_user() and not target_user.is_internal_user():
            send_request_to = user.assigned_to

            form = RequestForm(initial={
                'to_user': send_request_to,
                'request_type': UserRequest.READ,
                'model_type': UserRequest.USER,
                'for_url': request.build_absolute_uri(),
            })

            return render(request, 'form_template.html', {
                'title': 'Request For Access',
                'form': form,
                'readonly': True,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

    def post(self, request, user_id):

        user = request.user
        target_user = MyUser.objects.filter(id=user_id, is_active=True).exclude(username=MyUser.ANON).exclude(user_type=MyUser.ADMIN).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

        if user.is_internal_user() and not user.is_admin():
            send_request_to = user.assigned_to

            form = RequestForm(data={
                'to_user': send_request_to.id,
                'request_type': UserRequest.READ,
                'model_type': UserRequest.USER,
                'for_url': request.build_absolute_uri(),
            })

            if form.is_valid():
                user_request = form.save(commit=False)
                user_request.from_user = user
                user_request.user_obj = target_user

                if CommonHelpers.is_request_duplicate(user_request):
                    messages.warning(request, 'Request Already Sent')

                    return HttpResponseRedirect(reverse('app:HomeView'))

                user_request.save()

                messages.success(request, 'Request Sent To %s' % user_request.to_user)
                logger.info("User Profile View Request sent by %s for %s", str(user.username), str(target_user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))

            return render(request, 'form_template.html', {
                'title': 'Request For Access',
                'form': form,
                'readonly': True,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions for this',
            })


class UserProfileEdit(LoginAndOTPRequiredMixin, View):

    def get(self, request, user_id):

        user = request.user
        target_user = MyUser.objects.filter(id=user_id, is_active=True).exclude(username=MyUser.ANON).exclude(user_type=MyUser.ADMIN).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

        if user.has_perm('edit_user', target_user) or CommonHelpers.is_int_equal(user_id, user.id) or user.is_admin():
            form = EditUserProfileForm(instance=target_user, user_id=user_id)

            return render(request, 'form_template.html', {
                'title': 'Edit User Profile',
                'form': form,
            })

        elif user.is_internal_user() and not target_user.is_internal_user():
            send_request_to = user.assigned_to

            form = RequestForm(initial={
                'to_user': send_request_to,
                'request_type': UserRequest.UPDATE,
                'model_type': UserRequest.USER,
                'for_url': request.build_absolute_uri(),
            })

            return render(request, 'form_template.html', {
                'title': 'Request For Access',
                'form': form,
                'readonly': True,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

    def post(self, request, user_id):

        user = request.user
        target_user = MyUser.objects.filter(id=user_id, is_active=True).exclude(username=MyUser.ANON).exclude(user_type=MyUser.ADMIN).first()

        if not target_user:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })

        if user.is_admin():
            form = EditUserProfileForm(data=request.POST, user_id=user_id)

            if form.is_valid():
                edit_user = form.save(commit=False)
                edit_user.user = target_user
                edit_user.save()

                UserHelpers.update_user_from_edited_version(edit_user)

                messages.success(request, 'User Successfully Updated')
                logger.info("User Profile Edited by %s for %s", str(user.username), str(target_user.username))

                return HttpResponseRedirect(reverse('app:HomeView'))

            return render(request, 'form_template.html', {
                'title': 'Edit User Profile',
                'form': form,
            })

        elif user.has_perm('edit_user', target_user) or CommonHelpers.is_int_equal(user_id, user.id):
            remove_perm('edit_user', user, target_user)
            form = EditUserProfileForm(data=request.POST, user_id=user_id)

            if form.is_valid():
                edit_user = form.save(commit=False)
                edit_user.user = target_user
                edit_user.save()

                send_request_to = user.get_assigned_admin()

                form = RequestForm(data={
                    'to_user': send_request_to.id,
                    'request_type': UserRequest.COMPLETE_UPDATE,
                    'model_type': UserRequest.USER,
                    'for_url': request.build_absolute_uri(),
                })

                if form.is_valid():
                    user_request = form.save(commit=False)
                    user_request.from_user = user
                    user_request.user_obj = target_user

                    if CommonHelpers.is_request_duplicate(user_request):
                        messages.warning(request, 'Request Already Sent')

                        return HttpResponseRedirect(reverse('app:HomeView'))

                    user_request.save()

                    messages.success(request, 'Request Sent To %s' % user_request.to_user)
                    logger.info("User Profile Edit Request sent by %s for %s to %s", str(user.username), str(target_user.username), str(user_request.to_user))

                    return HttpResponseRedirect(reverse('app:HomeView'))

            return render(request, 'form_template.html', {
                'title': 'Edit User Profile',
                'form': form,
            })

        elif user.is_internal_user() and not target_user.is_internal_user():
            send_request_to = user.assigned_to

            form = RequestForm(data={
                'to_user': send_request_to.id,
                'request_type': UserRequest.UPDATE,
                'model_type': UserRequest.USER,
                'for_url': request.build_absolute_uri(),
            })

            if form.is_valid():
                user_request = form.save(commit=False)
                user_request.from_user = user
                user_request.user_obj = target_user

                if CommonHelpers.is_request_duplicate(user_request):
                    messages.warning(request, 'Request Already Sent')

                    return HttpResponseRedirect(reverse('app:HomeView'))

                user_request.save()

                messages.success(request, 'Request Sent To %s' % user_request.to_user)
                logger.info("User Profile Edit Access Request sent by %s for %s to %s", str(user.username), str(target_user.username), str(user_request.to_user))

                return HttpResponseRedirect(reverse('app:HomeView'))

            return render(request, 'form_template.html', {
                'title': 'Request For Access',
                'form': form,
                'readonly': True,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions to view this',
            })


class UserDelete(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        if user.is_admin():
            form = UserDeleteForm()

            return render(request, 'form_template.html', {
                'title': 'Delete User',
                'form': form,
            })

        elif not user.is_internal_user():
            form = VerifyOTPForm()

            return render(request, 'form_template.html', {
                'title': 'Confirm OTP To Send Delete Request',
                'form': form,
            })

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions for this.',
            })

    def post(self, request):

        user = request.user

        if user.is_admin():
            form = UserDeleteForm(request.POST)

            if form.is_valid():
                target_user = form.cleaned_data['user']
                if UserHelpers.safely_delete_user(target_user):

                    messages.success(request, 'User Deleted')
                    logger.info('User %s deleted by %s', str(target_user.username), str(user.username))

                    return HttpResponseRedirect(reverse('app:HomeView'))

                else:
                    return render(request, 'error.html', {
                        'err': 'User could not be deleted',
                    })

            return render(request, 'form_template.html', {
                'title': 'Delete User',
                'form': form,
            })

        elif not user.is_internal_user():
            form = VerifyOTPForm(request, data=request.POST)

            if form.is_valid():
                send_request_to = user.assigned_to

                form = RequestForm(data={
                    'to_user': send_request_to.id,
                    'request_type': UserRequest.DELETE,
                    'model_type': UserRequest.USER,
                })

                if form.is_valid():
                    user_request = form.save(commit=False)
                    user_request.from_user = user
                    user_request.user_obj = user

                    if CommonHelpers.is_request_duplicate(user_request):
                        messages.warning(request, 'Request Already Sent')

                        return HttpResponseRedirect(reverse('app:HomeView'))

                    user_request.save()

                    messages.success(request, 'Request Sent To %s' % user_request.to_user)
                    logger.info("User Delete Request sent by %s for %s to %s", str(user.username), str(user.username), str(user_request.to_user))

                    return HttpResponseRedirect(reverse('app:HomeView'))

                else:
                    return render(request, 'error.html', {
                        'err': 'User could not be deleted',
                    })

            else:
                messages.error(request, 'Incorrect OTP')

                return HttpResponseRedirect(reverse('app:HomeView'))

        else:
            return render(request, 'error.html', {
                'err': 'You do not have permissions for this.',
            })


class UserRequestsReceivedView(LoginAndOTPRequiredMixin, View):

    def get(self, request):

        user = request.user

        links = UserHelpers.get_unapproved_user_requests_to_user(user)

        return render(request, 'list_template.html', {
            'title': 'Requests Received',
            'links': links,
        })


class UserRequestView(LoginAndOTPRequiredMixin, View):

    def get(self, request, user_request_id):

        user = request.user

        # Takes care of case that user == user_request.to_user
        user_request = UserHelpers.get_user_request_to_user_using_id(user_request_id, user)

        if user_request:
            form = RequestForm(instance=user_request)

            hide_btn = False
            if user_request.is_approved:
                hide_btn = True

            extra_form = None
            if user_request.request_type == UserRequest.COMPLETE_UPDATE:
                edit_user = UserHelpers.get_edited_user(user_request.user_obj)
                extra_form = EditUserProfileForm(instance=edit_user, user_id=user_request.user_obj.id)

            return render(request, 'form_template.html', {
                'title': 'Request',
                'form': form,
                'readonly': True,
                'btn_title': 'Approve',
                'extra_btn_title': 'Decline',
                'hide_btn': hide_btn,
                'extra_form': extra_form,
            })

        return render(request, 'error.html', {
            'err': 'Does not exist or you cannot view',
        })

    def post(self, request, user_request_id):

        user = request.user

        # Takes care of case that user == user_request.to_user
        user_request = UserHelpers.get_user_request_to_user_using_id(user_request_id, user)

        if user_request:
            if 'Approve' in request.POST:
                approve_request = True
            elif 'Decline' in request.POST:
                approve_request = False
            else:
                return render(request, 'error.html', {
                    'err': 'You did something wrong, bro.'
                })

            if user_request.is_approved:
                return render(request, 'error.html', {
                    'err': 'Request Already Approved',
                })

            if approve_request:
                if UserHelpers.assign_permissions(user_request):
                    user_request.approve(user)

                    CommonHelpers.send_request_approval_mail(user_request)

                    messages.success(request, 'Request Approved')

                    # Intermediate Delete Request
                    if user_request.request_type == UserRequest.DELETE and user_request.model_type == UserRequest.USER:
                        messages.success(request, 'Request Sent To %s' % str(user_request.to_user.get_assigned_admin()))

                    # Delete completed
                    if user_request.request_type == UserRequest.COMPLETE_DELETE and user_request.model_type == UserRequest.USER:
                        logger.info('User %s deleted by %s', str(user_request.user_obj.username), str(user_request.to_user.username))

                    logger.info("User request %s approved by %s ", user_request.__str__(), str(user.username))

                    return HttpResponseRedirect(reverse('app:UserRequestsReceivedView'))

                return render(request, 'error.html', {
                    'err': 'Request could not be approved',
                })

            else:
                if not user_request.is_approved:
                    UserHelpers.delete_request(user_request)

                    CommonHelpers.send_request_declined_mail(user_request)

                    messages.success(request, 'Request Declined')

                    logger.info("User request %s declined by %s", user_request.__str__(), str(user.username))

                    return HttpResponseRedirect(reverse('app:UserRequestsReceivedView'))

                else:
                    return render(request, 'error.html', {
                        'err': 'Request cannot be declined because it is already approved.',
                    })

        return render(request, 'error.html', {
            'err': 'Does not exist',
        })
