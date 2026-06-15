import os

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Count, Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import escape

from activities.models import Activity
from attendance.models import Attendance

from .forms import (
    AdminUserUpdateForm,
    AdminSetupForm,
    CompleteProfileForm,
    EmailAuthenticationForm,
    RoleForm,
    UserRegistrationForm,
    UserProfileUpdateForm,
)
from .models import Role, User


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return render(request, "landing/index.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                "Registration successful. Please complete your profile.",
            )
            login(request, user)
            return redirect("accounts:complete-profile")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def admin_setup_view(request, secret):
    setup_secret = os.getenv("ADMIN_SETUP_SECRET", "").strip()
    if not setup_secret or secret != setup_secret:
        raise Http404

    if User.objects.filter(is_superuser=True).exists():
        raise Http404

    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = AdminSetupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Admin account created. You are now signed in.")
            login(request, user)
            return redirect("accounts:dashboard")
    else:
        form = AdminSetupForm()
    return render(request, "accounts/admin_setup.html", {"form": form})


def _staff_required(user):
    return user.can_manage_system


@login_required
def profile_view(request):
    recent_attendance = (
        Attendance.objects.filter(user=request.user)
        .select_related("activity")
        .order_by("-timestamp")[:10]
    )
    return render(
        request,
        "accounts/profile.html",
        {
            "recent_attendance": recent_attendance,
        },
    )


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = UserProfileUpdateForm(
            request.POST, request.FILES, instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile details updated successfully.")
            return redirect("accounts:profile")
    else:
        form = UserProfileUpdateForm(instance=request.user)
    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
def complete_profile_view(request):
    if request.user.is_profile_completed:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = CompleteProfileForm(
            request.POST, request.FILES, instance=request.user
        )
        if form.is_valid():
            user = form.save(commit=False)
            user.is_profile_completed = True
            user.save()
            messages.success(request, "Your profile has been completed successfully.")
            return redirect("accounts:dashboard")
    else:
        form = CompleteProfileForm(instance=request.user)

    return render(request, "accounts/complete_profile.html", {"form": form})


@login_required
def dashboard_view(request):
    if request.user.can_manage_system:
        activities = Activity.objects.order_by("-date")[:8]
        activity_attendance = list(
            Attendance.objects.values("activity__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        context = {
            "activities": activities,
            "activity_attendance": activity_attendance,
            "total_users": User.objects.count(),
            "total_records": Attendance.objects.count(),
            "total_roles": Role.objects.count(),
        }
        return render(request, "accounts/admin_dashboard.html", context)

    return render(request, "accounts/user_dashboard.html")


def _dt_get_int(get, name, default, min_v, max_v=None):
    try:
        v = int(get.get(name, default))
    except (TypeError, ValueError):
        return default
    if v < min_v:
        return min_v
    if max_v is not None and v > max_v:
        return max_v
    return v


def _user_list_search_filter(q: str) -> Q:
    return (
        Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(email__icontains=q)
        | Q(nickname__icontains=q)
        | Q(mobile_number__icontains=q)
    )


def _user_list_order(qs, col: int, direction: str):
    asc = direction == "asc"
    if col == 1:
        o = "email" if asc else "-email"
        return qs.order_by(o, "id" if asc else "-id")
    if col == 2:
        o = "mobile_number" if asc else "-mobile_number"
        return qs.order_by(o, "id" if asc else "-id")
    if col in (3, 4):
        return qs.order_by("last_name", "first_name", "id")
    o1 = "last_name" if asc else "-last_name"
    o2 = "first_name" if asc else "-first_name"
    return qs.order_by(o1, o2, "id" if asc else "-id")


@login_required
@user_passes_test(_staff_required)
def user_management_view(request):
    return render(
        request,
        "accounts/user_management.html",
    )


@login_required
@user_passes_test(_staff_required)
def user_management_data_view(request):
    """DataTables server-side: small pages, no full result set in the browser."""
    draw = _dt_get_int(request.GET, "draw", 0, 0, 10_000_000)
    start = _dt_get_int(request.GET, "start", 0, 0, 1_000_000)
    default_len = 12
    max_len = 100
    length = _dt_get_int(request.GET, "length", default_len, 1, max_len)

    try:
        order_col = int(request.GET.get("order[0][column]", 0))
    except (TypeError, ValueError):
        order_col = 0
    order_dir = (request.GET.get("order[0][dir]", "asc") or "asc").lower()
    if order_dir not in ("asc", "desc"):
        order_dir = "asc"

    q = (request.GET.get("search[value]") or "").strip()

    base = User.objects.all()
    records_total = base.count()
    if q:
        filtered = base.filter(_user_list_search_filter(q))
        records_filtered = filtered.count()
    else:
        filtered = base
        records_filtered = records_total

    ordered = _user_list_order(filtered, order_col, order_dir)
    user_slice = list(
        ordered[start : start + length].only(
            "id",
            "first_name",
            "last_name",
            "email",
            "mobile_number",
        ).prefetch_related(
            Prefetch(
                "roles",
                queryset=Role.objects.filter(is_active=True)
                .only("name", "id")
                .order_by("name"),
            )
        )
    )

    def roles_cell(user_obj) -> str:
        badges = [
            f'<span class="badge bg-primary me-1">{escape(r.name)}</span>'
            for r in user_obj.roles.all()
        ]
        if not badges:
            return '<span class="text-muted">No roles</span>'
        return "".join(badges)

    def row_data(user_obj) -> list:
        edit_href = reverse("accounts:user-edit", args=[user_obj.pk])
        return [
            escape(user_obj.full_name) or "—",
            escape(user_obj.email) or "—",
            escape(user_obj.mobile_number) or "—",
            roles_cell(user_obj),
            f'<a class="btn btn-sm btn-outline-secondary" href="{edit_href}">Edit User</a>',
        ]

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": [row_data(u) for u in user_slice],
        }
    )


@login_required
@user_passes_test(_staff_required)
def user_edit_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = AdminUserUpdateForm(
            request.POST,
            request.FILES,
            instance=user_obj,
        )
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated profile for {user_obj.full_name}.")
            return redirect("accounts:user-management")
    else:
        form = AdminUserUpdateForm(instance=user_obj)
    return render(
        request,
        "accounts/user_edit_admin.html",
        {"form": form, "user_obj": user_obj},
    )


@login_required
@user_passes_test(_staff_required)
def role_library_view(request):
    roles = (
        Role.objects.annotate(user_count=Count("users", distinct=True))
        .order_by("name")
    )
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Role “{form.cleaned_data.get('name')}” created."
            )
            return redirect("accounts:role-library")
    else:
        form = RoleForm()
    return render(
        request,
        "accounts/role_library.html",
        {"roles": roles, "form": form},
    )


@login_required
@user_passes_test(_staff_required)
def role_edit_view(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, "Role updated.")
            return redirect("accounts:role-library")
    else:
        form = RoleForm(instance=role)
    return render(
        request,
        "accounts/role_edit.html",
        {"form": form, "role": role},
    )


@login_required
@user_passes_test(_staff_required)
def role_delete_view(request, role_id):
    if request.method != "POST":
        return redirect("accounts:role-library")
    role = get_object_or_404(Role, id=role_id)
    name = role.name
    role.delete()
    messages.success(request, f"Role “{name}” deleted.")
    return redirect("accounts:role-library")
