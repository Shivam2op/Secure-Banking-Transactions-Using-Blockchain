from django.contrib.auth import logout
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


class LoginAndOTPRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        """Allows users if they're authenticated and verified, or if they are superuser, or if they have switched into someone else's account"""

        if not (request.user.is_authenticated and request.user.is_verified() or request.user.is_superuser):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated and self.request.user.is_verified():
            raise PermissionDenied(self.get_permission_denied_message())

        elif self.request.user.is_authenticated:
            logout(self.request)

        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
