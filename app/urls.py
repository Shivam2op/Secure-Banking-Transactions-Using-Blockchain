from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.urls import re_path

from app.views.HomeViews import HomeView, DashboardView
from app.views.Logging.LoggingViews import SystemLogsView, TransactionLogsView, SystemLogsDate, TransactionLogsDate
from app.views.PKI.PKIViews import PkiView, EncryptView, DecryptView, GenerateRSA, UserPublicKeyAPI
from app.views.PiiViews import PiiView, GovtPIIAccess, ViewPii
from app.views.TestViews import TestErrors
from app.views.accounts.AccountViews import UserAccountsView, AccountView, UsersHavingAccountView, \
    UserAddAccountView
from app.views.known_accounts.KnownAccountsViews import EnterKnownAccountsView, ViewKnownAccounts
from app.views.login.LoginViews import MyLoginView
from app.views.payment_accounts.PaymentAccountViews import EnterPaymentAccountsView, ViewPaymentccounts, \
    RemovePaymentAccounts
from app.views.signup.SignUpViews import SignUp, OTPImage, UserConfirmation, \
    PasswordResetConfirm, PasswordResetRequestView
from app.views.JavaScriptDisableViews import JavaScriptDisableView

from app.views.su.SuViews import CustomSuLogout, CustomSuLogin, CustomSuLoginAsUser
from app.views.transactions.TransactionViews import TransactionRequest, TransactionView, \
    TransactionPending, TransactionCompleted, TransactionLocator, TransactionRisky
from app.views.users.UserViews import AllUsersView, UserProfile, UserRequestsReceivedView, \
    UserRequestView, UserProfileEdit, UserDelete

app_name = 'app'

urlpatterns = [
    re_path(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),

    re_path(r'^$', HomeView.as_view(), name='HomeView'),
    re_path(r'^login/$', MyLoginView.as_view(), name='MyLoginView'),
    re_path(r'^logout/$', LogoutView.as_view(), name='LogoutView'),

    re_path(r'^api/superuser/generate-rsa/$', GenerateRSA.as_view(), name='GenerateRSA'),

    re_path(r'^pki/$', PkiView.as_view(), name='PkiView'),
    re_path(r'^api/pki/$', UserPublicKeyAPI.as_view(), name='UserPublicKeyAPI'),
    # re_path(r'^encrypt/$', EncryptView.as_view(), name='EncryptView'),
    # re_path(r'^decrypt/$', DecryptView.as_view(), name='DecryptView'),

    # re_path(r'^change-password/$', ChangePassword.as_view(), name='ChangePassword'),
    re_path(r'^password-reset-initiate/$', PasswordResetRequestView.as_view(), name='PasswordResetRequestView'),
    re_path(r'^password-reset-confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',PasswordResetConfirm.as_view(), name='confirm_password_reset'),

    re_path(r'^signup/$', SignUp.as_view(), name='SignUp'),
    re_path(r'^otp-image/$', OTPImage.as_view(), name='OTPImage'),
    re_path(r'^dashboard/$', DashboardView.as_view(), name='DashboardView'),
  
    re_path(r'^jserror/',JavaScriptDisableView.as_view(), name="JavaScriptDisable"),

    re_path(r'^user/all/$', AllUsersView.as_view(), name='AllUsersView'),
    re_path(r'^user/(?P<user_id>[0-9]+)/$', UserProfile.as_view(), name='UserProfile'),
    re_path(r'^user/(?P<user_id>[0-9]+)/edit/$', UserProfileEdit.as_view(), name='UserProfileEdit'),
    re_path(r'^user/delete/$', UserDelete.as_view(), name='UserDelete'),

    re_path(r'^user/pii/$',ViewPii.as_view(), name='ViewPii'),
    re_path(r'^pii/(?P<user_id>[0-9]+)/$', PiiView.as_view(), name='Pii'),
    re_path(r'^pii/(?P<uidb1>[0-9A-Za-z_\-]+)/(?P<uidb2>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', GovtPIIAccess.as_view(), name='GovtPIIAccess'),

    re_path(r'^enter-known-account/$', EnterKnownAccountsView.as_view(), name='enter_known_account'),
    re_path(r'^view-known-account/$', ViewKnownAccounts.as_view(), name='view_known_account'),
    re_path(r'^enter-payment-account/$', EnterPaymentAccountsView.as_view(), name='enter_payment_account'),
    re_path(r'^view-payment-account/$', ViewPaymentccounts.as_view(), name='view_payment_account'),
    re_path(r'^remove-payment-account/$', RemovePaymentAccounts.as_view(), name='remove_payment_account' ),

    re_path(r'^user/request/$', UserRequestsReceivedView.as_view(), name='UserRequestsReceivedView'),
    re_path(r'^user/request/(?P<user_request_id>[0-9]+)/$', UserRequestView.as_view(), name='UserRequestView'),

    re_path(r'^account/(?P<user_id>[0-9]+)/add/$', UserAddAccountView.as_view(), name='UserAddAccountView'),
    re_path(r'^account/(?P<user_id>[0-9]+)/all/$', UserAccountsView.as_view(), name='UserAccountsView'),
    re_path(r'^account/(?P<user_id>[0-9]+)/(?P<account_id>[0-9]+)/$', AccountView.as_view(), name='AccountView'),
    re_path(r'^account/all/$', UsersHavingAccountView.as_view(), name='UsersHavingAccountView'),

    re_path(r'^transaction/risky/$', TransactionRisky.as_view(), name='TransactionRisky'),
    re_path(r'^transaction/pending/$', TransactionPending.as_view(), name='TransactionPending'),
    re_path(r'^transaction/completed/$', TransactionCompleted.as_view(), name='TransactionCompleted'),
    re_path(r'^transaction/create/$', TransactionRequest.as_view(), name='TransactionRequest'),
    re_path(r'^transaction/(?P<transaction_id>[0-9]+)/$', TransactionView.as_view(), name='TransactionView'),
    re_path(r'^transaction/locator/$', TransactionLocator.as_view(), name='TransactionLocator'),

    re_path(r'^confirm-account/(?P<uidb>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', UserConfirmation.as_view(), name='UserConfirmation'),

    re_path(r'^system-logs-files/$', SystemLogsView.as_view(), name='SystemLogsView'),
    re_path(r'^system-logs/(?P<log_id>[0-9]+)/$', SystemLogsDate.as_view(), name='SystemLogsDate'),
    re_path(r'^transaction-logs-files/$', TransactionLogsView.as_view(), name='TransactionLogsView'),
    re_path(r'^transaction-logs/(?P<log_id>[0-9]+)/$', TransactionLogsDate.as_view(), name='TransactionLogsDate'),

    # Switch User
    re_path(r'^switch-user/$', CustomSuLogout.as_view(), name='CustomSuLogout'),
    re_path(r'^switch-user/login/$', CustomSuLogin.as_view(), name='CustomSuLogin'),
    re_path(r'^switch-user/(?P<user_id>[0-9]+)/$', CustomSuLoginAsUser.as_view(), name='CustomSuLoginAsUser'),

    # Test Errors
    re_path(r'^test-errors/$', TestErrors.as_view(), name='TestErrors'),

    # Include built-in pages for authentication
    # re_path(r'^', include('django.contrib.auth.urls')),
]
