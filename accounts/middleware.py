from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve


class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_profile_completed:
            if request.path.startswith("/admin/") or request.path.startswith(
                settings.STATIC_URL
            ) or request.path.startswith(settings.MEDIA_URL):
                return self.get_response(request)

            try:
                match = resolve(request.path_info)
                current_view_name = match.view_name
            except Resolver404:
                current_view_name = ""

            exempt_views = {
                "accounts:complete-profile",
                "accounts:logout",
            }

            if current_view_name not in exempt_views:
                return redirect("accounts:complete-profile")

        return self.get_response(request)
