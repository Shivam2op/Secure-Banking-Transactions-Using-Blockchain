import os
from base64 import b64decode, b64encode

from Crypto import Hash
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from django.utils.crypto import get_random_string

from app.models import PublicKey
from bank.settings import BASE_DIR


def get_server_private_key():
    path = 'app/rsa/rsa_private.bin'
    #path = os.path.join(BASE_DIR, path)

    file = open(path, 'rb')
    passphrase = os.getenv('RSA_PASS')
    #passphrase = ("12345")
    key = RSA.import_key(file.read(), passphrase=passphrase)

    return key


def get_server_public_key():
    path = 'app/rsa/rsa_public.bin'
    #path = os.path.join(BASE_DIR, path)

    file = open(path, 'rb')
    passphrase = os.getenv('RSA_PASS')
    #passphrase = ("12345")
    key = RSA.import_key(file.read(), passphrase=passphrase)
    
    return key


def get_user_public_key(public_key):
    key = RSA.import_key(b64decode(public_key.publickey))

    return key


def encrypt_with_public_key(data, key):
    cipher = PKCS1_OAEP.new(key, Hash.SHA256.new())
    encrypted_data = cipher.encrypt(data.encode())

    return encrypted_data


def decrypt_with_private_key(data, key):
    cipher = PKCS1_OAEP.new(key, Hash.SHA256.new())
    decrypted_data = cipher.decrypt(b64decode(data)).decode()

    return decrypted_data


def get_encrypted_token(user):
    user_public_key = PublicKey.objects.filter(user=user).first()

    if user_public_key:
        user_public_key = get_user_public_key(user_public_key)
        data = get_random_string(20)
        server_public_key = get_server_public_key()

        user_encrypted_data = encrypt_with_public_key(data, user_public_key)
        server_encrypted_data = encrypt_with_public_key(data, server_public_key)

        user_encrypted_data = b64encode(user_encrypted_data).decode()
        server_encrypted_data = b64encode(server_encrypted_data).decode()

        return user_encrypted_data, server_encrypted_data

    return None, None


def get_decrypted_token(token):
    server_private_key = get_server_private_key()
    decrypted_token = decrypt_with_private_key(token, server_private_key)

    return decrypted_token


def get_pki_dictionary(edata):
    pki = dict()

    pki['edata'] = edata
    pki['public_key'] = b64encode(get_server_public_key().export_key('DER')).decode()

    return pki


def verify_pki(token1, token2):
    try:
        token1 = get_decrypted_token(token1)
        token2 = get_decrypted_token(token2)

        print(token1, token2)
        return token1 == token2

    except ValueError:
        return False
