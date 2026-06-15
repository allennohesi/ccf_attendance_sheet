import json
import mimetypes
import os
import urllib.parse
import urllib.request

from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

BLOB_API = "https://blob.vercel-storage.com"


def blob_storage_enabled():
    return bool(os.getenv("BLOB_READ_WRITE_TOKEN"))


def upload_blob(pathname, data, content_type="application/octet-stream", access="public"):
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise RuntimeError("BLOB_READ_WRITE_TOKEN is not set")

    pathname = pathname.lstrip("/")
    query = urllib.parse.urlencode({"access": access})
    url = f"{BLOB_API}/{pathname}?{query}"
    request = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "x-api-version": "7",
            "x-content-type": content_type,
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode())
    return payload["url"]


@deconstructible
class VercelBlobStorage(Storage):
    def _save(self, name, content):
        content.seek(0)
        body = content.read()
        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )
        return upload_blob(name, body, content_type=content_type)

    def url(self, name):
        return name

    def exists(self, name):
        return bool(name)

    def delete(self, name):
        return None

    def size(self, name):
        return 0

    def get_available_name(self, name, max_length=None):
        return name
