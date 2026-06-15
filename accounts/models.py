import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class RoleCode(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    PARTICIPANT = "PARTICIPANT", "Participant"
    MEMBER = "MEMBER", "Member"
    VOLUNTEER = "VOLUNTEER", "Volunteer"
    DGROUP_LEADER = "DGROUP_LEADER", "DGroup Leader"


class Role(models.Model):
    code = models.SlugField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    username = None
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=50, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    birth_month = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    life_stage = models.CharField(max_length=100, blank=True)
    home_address = models.CharField(max_length=255, blank=True)
    work = models.CharField(max_length=150, blank=True)
    work_area = models.CharField(max_length=150, blank=True)
    social_media = models.CharField(max_length=255, blank=True)
    how_did_you_learn = models.CharField(max_length=255, blank=True)
    is_part_of_dgroup = models.BooleanField(default=False)
    dgroup_leader = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dgroup_members",
    )
    roles = models.ManyToManyField(
        "Role",
        related_name="users",
        blank=True,
        # NOTE: `accounts_user_groups` is used by AbstractUser.groups M2M; use a unique table name
        db_table="accounts_user_role_memberships",
    )
    is_profile_completed = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    qr_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def roles_display(self):
        if not self.pk:
            return "-"
        role_names = list(
            self.roles.filter(is_active=True)
            .order_by("name")
            .values_list("name", flat=True)
        )
        return ", ".join(role_names) if role_names else "-"

    @property
    def has_admin_role(self):
        if not self.pk:
            return False
        return self.roles.filter(code=RoleCode.ADMIN).exists()

    @property
    def can_manage_system(self):
        return self.is_superuser or self.is_staff or self.has_admin_role
