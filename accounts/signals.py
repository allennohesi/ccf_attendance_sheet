from io import BytesIO

import qrcode
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def create_user_qr_code(sender, instance, created, **kwargs):
    if not created or instance.qr_code:
        return

    qr_image = qrcode.make(str(instance.qr_uuid))
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    buffer.seek(0)
    filename = f"{instance.qr_uuid}.png"
    instance.qr_code.save(filename, File(buffer), save=True)
