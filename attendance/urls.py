from django.urls import path

from .views import (
    delete_attendance_record,
    scan_attendance_api,
    scan_attendance_view,
)

app_name = "attendance"

urlpatterns = [
    path("scan/<int:activity_id>/", scan_attendance_view, name="scan"),
    path("scan/<int:activity_id>/api/", scan_attendance_api, name="scan-api"),
    path(
        "activity/<int:activity_id>/attendance/<int:attendance_id>/delete/",
        delete_attendance_record,
        name="attendance-delete",
    ),
]
