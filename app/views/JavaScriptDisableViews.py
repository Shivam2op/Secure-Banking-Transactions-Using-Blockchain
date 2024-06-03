from django.contrib.auth import logout
from django.shortcuts import render
from django.views.generic.base import View


class JavaScriptDisableView(View):
    def get(self, request):

        user = request.user
        if user.is_authenticated:
            logout(request)

        return render(request, 'JSDisable.html', {
            'err': 'You Cannot Disable JavaScript on SBS. Please Enable it and Try Again.',
        })
