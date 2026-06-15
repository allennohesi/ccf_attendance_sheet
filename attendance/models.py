from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "activity"],
                name="unique_user_attendance_per_activity",
            )
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.email} - {self.activity.name}"
