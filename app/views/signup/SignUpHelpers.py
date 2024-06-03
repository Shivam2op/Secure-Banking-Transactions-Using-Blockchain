from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_otp.plugins.otp_totp.models import TOTPDevice


def get_qrcode(user_id):
    device = get_otp_device(user_id)

    try:
        import qrcode
        import qrcode.image.svg

        img = qrcode.make(device.config_url, image_factory=qrcode.image.svg.SvgImage)

        response = HttpResponse(content_type='image/svg+xml')
        img.save(response)
    except ImportError:
        response = HttpResponse('', status=503)

    return response


def get_otp_device(user_id):
    device = get_object_or_404(TOTPDevice, user_id=user_id)

    return device


def is_otp_device_confirmed(user_id):
    device = get_otp_device(user_id)

    return device.confirmed
