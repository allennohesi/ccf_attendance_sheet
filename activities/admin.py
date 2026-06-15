from django.contrib import admin
from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "location", "created_by")
    search_fields = ("name", "location")
    list_filter = ("date",)
