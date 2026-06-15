from django.urls import path

from .views import (
    ActivityAttendanceExportView,
    ActivityCreateView,
    ActivityDeleteView,
    ActivityDetailView,
    ActivityListView,
    ActivityUpdateView,
)

app_name = "activities"

urlpatterns = [
    path("", ActivityListView.as_view(), name="list"),
    path("create/", ActivityCreateView.as_view(), name="create"),
    path("<int:pk>/", ActivityDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", ActivityUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", ActivityDeleteView.as_view(), name="delete"),
    path("<int:pk>/export/", ActivityAttendanceExportView.as_view(), name="export"),
]
