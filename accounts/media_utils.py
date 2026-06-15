import os

from django.conf import settings


def local_media_enabled():
    if os.getenv("VERCEL"):
        return False
    try:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        probe = settings.MEDIA_ROOT / ".write_probe"
        probe.write_text("1")
        probe.unlink()
        return True
    except OSError:
        return False
