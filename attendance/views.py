import json
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from activities.models import Activity
from accounts.models import User

from .models import Attendance


def _staff_required(user):
    return user.can_manage_system


@login_required
@user_passes_test(_staff_required)
def scan_attendance_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    return render(request, "attendance/scan_attendance.html", {"activity": activity})


@login_required
@user_passes_test(_staff_required)
@require_POST
def scan_attendance_api(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        qr_uuid = payload.get("qr_uuid")
        parsed_uuid = uuid.UUID(qr_uuid)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "message": "Invalid QR payload."}, status=400)

    try:
        user = User.objects.get(qr_uuid=parsed_uuid)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "message": "No user found for this QR."}, status=404)

    attendance, created = Attendance.objects.get_or_create(
        user=user,
        activity=activity,
        defaults={"status": Attendance.Status.PRESENT},
    )

    if not created:
        return JsonResponse(
            {
                "ok": False,
                "message": f"{user.full_name} already scanned for this activity.",
            },
            status=409,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": f"Attendance recorded for {user.full_name}.",
            "timestamp": attendance.timestamp.isoformat(),
        }
    )


@login_required
@user_passes_test(_staff_required)
@require_POST
def delete_attendance_record(request, activity_id, attendance_id):
    activity = get_object_or_404(Activity, id=activity_id)
    record = get_object_or_404(
        Attendance.objects.filter(activity=activity),
        id=attendance_id,
    )
    who = record.user.full_name
    record.delete()
    messages.success(
        request,
        f"Removed {who} from the attendance list for {activity.name}.",
    )
    return redirect("activities:detail", pk=activity_id)
