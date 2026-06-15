from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    filter_horizontal = ("roles",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "roles_display",
        "is_profile_completed",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_profile_completed", "is_staff", "is_superuser", "is_active")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name", "nickname")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "nickname",
                    "avatar",
                    "mobile_number",
                )
            },
        ),
        (
            "Profile details",
            {
                "fields": (
                    "gender",
                    "birth_month",
                    "birth_year",
                    "life_stage",
                    "home_address",
                    "work",
                    "work_area",
                    "social_media",
                    "how_did_you_learn",
                    "is_part_of_dgroup",
                    "dgroup_leader",
                    "qr_uuid",
                    "qr_code",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "roles",
                    "is_profile_completed",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )

    def roles_display(self, obj):
        return obj.roles_display

    roles_display.short_description = "Roles"
