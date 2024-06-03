from app.views import CommonHelpers


def su_login_by_admin(user):
    if user.is_authenticated and user.is_verified() and user.is_admin() or user.is_superuser:
        return True

    raise PermissionError('You do not have permissions for this')


def login_action(request, user):
    CommonHelpers.login_and_verify_without_otp(request, user)
