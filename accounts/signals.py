from io import BytesIO

import qrcode
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


def build_qr_png(qr_uuid) -> bytes:
    qr_image = qrcode.make(str(qr_uuid))
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    return buffer.getvalue()


@receiver(post_save, sender=User)
def create_user_qr_code(sender, instance, created, **kwargs):
    if not created or instance.qr_code:
        return

    try:
        filename = f"{instance.qr_uuid}.png"
        instance.qr_code.save(filename, File(BytesIO(build_qr_png(instance.qr_uuid))), save=True)
    except OSError:
        # Vercel/serverless has a read-only filesystem; QR is served on demand instead.
        pass
