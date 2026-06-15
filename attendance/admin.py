from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "activity", "timestamp", "status")
    list_filter = ("status", "activity")
    search_fields = ("user__email", "user__first_name", "user__last_name")
