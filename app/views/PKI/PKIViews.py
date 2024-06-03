import os
from base64 import b64decode, b64encode
from Crypto import Hash
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from app.forms import TransactionForms
from app.forms.PKIForms import PKIForms
from app.mixins import LoginAndOTPRequiredMixin
from app.models import PublicKey
from django.db import transaction as db_transaction
import logging

from bank.settings import BASE_DIR


logger = logging.getLogger(__name__)


class PkiView(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        form = TransactionForms.VerifyOTPForm()

        return render(request, 'form_template.html', {
            'title': 'Confirm OTP',
            'form': form,
            'form_virtual_keyboard': True,
        })

    def post(self, request):
        form = TransactionForms.VerifyOTPForm(request, data=request.POST)

        if form.is_valid():
            request.session['_otp_verified'] = True

            return render(request, 'create_pki.html', {
                'title': 'Configuring PKI',
            })

        messages.error(request, 'Incorrect OTP')
        return HttpResponseRedirect(reverse('app:HomeView'))


class UserPublicKeyAPI(LoginAndOTPRequiredMixin, View):

    def post(self, request):
        user = request.user

        otp_verified = request.session.get('_otp_verified', False)
        form = PKIForms(data=request.POST)
        if otp_verified and form.is_valid():
            with db_transaction.atomic():
                PublicKey.objects.filter(user=user).select_for_update().delete()

            instance = form.save(commit=False)
            instance.user = user
            instance.save()

            logger.info("PKI reset : %s", str(user.username))

            logout(request)
            return HttpResponse("Key added")

        logout(request)
        return HttpResponse("Key Not added")


class GenerateRSA(View):

    def get(self, request):

        user = request.user

        if user.is_superuser:
            key = RSA.generate(1024)

            path = 'app/rsa/rsa_private.bin'
            path = os.path.join(BASE_DIR, path)
            private_file = open(path, 'wb')

            path = 'app/rsa/rsa_public.bin'
            path = os.path.join(BASE_DIR, path)
            public_file = open(path, 'wb')

            passphrase = os.getenv('RSA_PASS')

            encrypted_private_key = key.export_key(passphrase=passphrase)
            private_file.write(encrypted_private_key)

            encrypted_public_key = key.publickey().export_key(passphrase=passphrase)
            public_file.write(encrypted_public_key)

            private_file.close()
            public_file.close()

            return HttpResponse('Success')

        else:
            raise Http404


# Unused
class DecryptView(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        public_key = PublicKey.objects.filter(user=request.user).first()

        key = RSA.import_key(b64decode(public_key.publickey))
        h = Hash.SHA256.new()
        cipher = PKCS1_OAEP.new(key, h)

        encrypted_data = cipher.encrypt(b'hi')
        encrypted_data = b64encode(encrypted_data).decode()

        return render(request, 'getprivatekeyanddecrpt.html', {
            "edata": encrypted_data,
        })


# Unused
class EncryptView(LoginAndOTPRequiredMixin, View):

    def get(self, request):
        data = "SBS IS LOVE"
        publickey = PublicKey.objects.filter(user=request.user).first()

        return render(request, 'encryptdata.html', {
            "publickey": publickey,
            "data": data
        })