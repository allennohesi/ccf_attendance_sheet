from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from accounts.views import admin_setup_view

urlpatterns = [
    path("admin/register/", admin_setup_view, name="admin-register"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("activities/", include("activities.urls")),
    path("attendance/", include("attendance.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
