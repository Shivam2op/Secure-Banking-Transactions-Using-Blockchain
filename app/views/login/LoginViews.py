from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from axes.decorators import axes_dispatch
from django_otp.views import LoginView
from app.forms.LoginForms import MyAuthenticationForm

@method_decorator(axes_dispatch, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class MyLoginView(LoginView):

    template_name = 'login.html'
    authentication_form = MyAuthenticationForm
    redirect_authenticated_user = True








