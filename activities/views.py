import csv

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone as django_timezone
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from attendance.models import Attendance

from .forms import ActivityForm
from .models import Activity


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can_manage_system


class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = "activities/activity_list.html"
    context_object_name = "activities"


class ActivityCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = "activities/activity_form.html"
    success_url = reverse_lazy("activities:list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ActivityUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = "activities/activity_form.html"
    success_url = reverse_lazy("activities:list")


class ActivityDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Activity
    template_name = "activities/activity_confirm_delete.html"
    success_url = reverse_lazy("activities:list")


class ActivityDetailView(LoginRequiredMixin, DetailView):
    model = Activity
    template_name = "activities/activity_detail.html"
    context_object_name = "activity"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_manager = user.is_authenticated and user.can_manage_system
        context["can_view_full_attendance"] = is_manager
        if is_manager:
            context["attendance_records"] = Attendance.objects.filter(
                activity=self.object
            ).select_related("user")
            context["my_attendance"] = None
        else:
            context["attendance_records"] = Attendance.objects.none()
            context["my_attendance"] = (
                Attendance.objects.filter(
                    activity=self.object,
                    user=user,
                )
                .select_related("user")
                .first()
            )
        return context


class ActivityAttendanceExportView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Activity

    def get(self, request, *args, **kwargs):
        activity = self.get_object()
        attendance = (
            Attendance.objects.filter(activity=activity)
            .select_related("user", "user__dgroup_leader")
            .order_by("user__last_name", "user__first_name", "timestamp")
        )

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="{activity.name}_attendance.csv"'
        )
        # UTF-8 BOM so Excel on Windows opens UTF-8 without garbled text
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(
            [
                "First name",
                "Last name",
                "Nickname",
                "Email address",
                "Mobile number",
                "Gender",
                "Birth month",
                "Birth year",
                "Life stage",
                "Home address",
                "Work",
                "Work area",
                "Social media (FB / Insta / etc.)",
                "How did you learn (about the ministry / CCF)",
                "Part of a discipleship group (D-group)",
                "D-group leader",
                "Attendance recorded (timestamp)",
                "Attendance status",
            ]
        )
        for item in attendance:
            u = item.user
            leader = u.dgroup_leader
            if leader is not None:
                leader_name = f"{leader.full_name} ({leader.email})"
            else:
                leader_name = ""
            row = [
                u.first_name,
                u.last_name,
                u.nickname,
                u.email,
                u.mobile_number,
                u.get_gender_display() if u.gender else "",
                u.birth_month if u.birth_month is not None else "",
                u.birth_year if u.birth_year is not None else "",
                u.life_stage,
                u.home_address,
                u.work,
                u.work_area,
                u.social_media,
                u.how_did_you_learn,
                "Yes" if u.is_part_of_dgroup else "No",
                leader_name,
                (
                    django_timezone.localtime(item.timestamp).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if item.timestamp
                    else ""
                ),
                item.get_status_display(),
            ]
            writer.writerow(row)
        return response
