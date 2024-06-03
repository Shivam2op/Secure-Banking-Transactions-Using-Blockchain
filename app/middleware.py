from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin


class ActiveUserMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            logout(request)
