from django.contrib.auth.views import LogoutView, PasswordChangeDoneView, PasswordChangeView
from django.urls import path, reverse_lazy

from .forms import TailwindPasswordChangeForm

from .views import (
    UserLoginView,
    complete_profile_view,
    dashboard_view,
    edit_profile_view,
    home,
    profile_view,
    register_view,
    role_delete_view,
    role_edit_view,
    role_library_view,
    user_edit_view,
    user_management_data_view,
    user_management_view,
)

app_name = "accounts"

urlpatterns = [
    path("", home, name="home"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", register_view, name="register"),
    path("complete-profile/", complete_profile_view, name="complete-profile"),
    path("profile/", profile_view, name="profile"),
    path("profile/edit/", edit_profile_view, name="edit-profile"),
    path(
        "profile/change-password/",
        PasswordChangeView.as_view(
            template_name="accounts/change_password.html",
            form_class=TailwindPasswordChangeForm,
            success_url=reverse_lazy("accounts:change-password-done"),
        ),
        name="change-password",
    ),
    path(
        "profile/change-password/done/",
        PasswordChangeDoneView.as_view(
            template_name="accounts/change_password_done.html",
        ),
        name="change-password-done",
    ),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("user-management/", user_management_view, name="user-management"),
    path("user-management/data/", user_management_data_view, name="user-management-data"),
    path("roles/library/", role_library_view, name="role-library"),
    path("roles/<int:role_id>/edit/", role_edit_view, name="role-edit"),
    path("roles/<int:role_id>/delete/", role_delete_view, name="role-delete"),
    path("user-management/<int:user_id>/edit/", user_edit_view, name="user-edit"),
]
