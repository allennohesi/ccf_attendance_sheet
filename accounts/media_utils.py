from .storage import blob_storage_enabled


def local_media_enabled():
    if blob_storage_enabled():
        return False
    import os

    from django.conf import settings

    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return False
    try:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        probe = settings.MEDIA_ROOT / ".write_probe"
        probe.write_text("1")
        probe.unlink()
        return True
    except OSError:
        return False


def media_uploads_enabled():
    return local_media_enabled() or blob_storage_enabled()
