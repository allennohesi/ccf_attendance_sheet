import uuid

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)

from .field_themes import (
    TW_FILE,
    TW_INPUT,
    TW_SELECT,
    TW_SELECT_MULTI_ROLES,
    TW_TEXTAREA,
)
from .media_utils import local_media_enabled
from .models import Role, RoleCode, User


class AvatarSaveMixin:
    def _prepare_avatar_for_save(self, user):
        if local_media_enabled() or not self.files.get("avatar"):
            return user
        if user.pk:
            user.avatar = User.objects.only("avatar").get(pk=user.pk).avatar
        else:
            user.avatar = None
        return user

    def save(self, commit=True):
        user = super().save(commit=False)
        user = self._prepare_avatar_for_save(user)
        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user


def _configure_avatar_field(field):
    if local_media_enabled():
        return
    field.required = False
    field.help_text = "Photo upload is not available on this server. Your initials will be shown instead."
    field.disabled = True


class StyledFormMixin:
    def style_fields(self):
        for _name, field in self.fields.items():
            self._apply_field_style(field)

    def _apply_field_style(self, field):
        w = field.widget
        if isinstance(w, forms.HiddenInput):
            return
        if isinstance(w, forms.Textarea):
            w.attrs["class"] = TW_TEXTAREA
        elif isinstance(w, forms.Select):
            w.attrs["class"] = TW_SELECT
        elif isinstance(w, forms.SelectMultiple):
            w.attrs["class"] = TW_SELECT_MULTI_ROLES
        elif isinstance(w, (forms.ClearableFileInput, forms.FileInput)):
            w.attrs["class"] = TW_FILE
        else:
            w.attrs["class"] = TW_INPUT


YES_NO_CHOICES = (
    (True, "Yes"),
    (False, "No"),
)

ACTIVE_INACTIVE = (
    (True, "Active"),
    (False, "Inactive"),
)


class UserRegistrationForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "mobile_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields["mobile_number"].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = f"pending-{uuid.uuid4()}@placeholder.local"
        if commit:
            user.save()
            default_role, _ = Role.objects.get_or_create(
                code=RoleCode.PARTICIPANT,
                defaults={"name": "Participant", "is_active": True},
            )
            user.roles.set([default_role])
        return user


class AdminSetupForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def save(self, commit=True):
        user = User.objects.create_superuser(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
        )
        user.is_profile_completed = True
        user.save(update_fields=["is_profile_completed"])

        admin_role = Role.objects.filter(pk=1).first()
        if admin_role is None:
            admin_role, _ = Role.objects.get_or_create(
                code=RoleCode.ADMIN,
                defaults={"name": "Admin", "is_active": True},
            )
        user.roles.set([admin_role])
        self.instance = user
        return user


class CompleteProfileForm(AvatarSaveMixin, StyledFormMixin, forms.ModelForm):
    social_media = forms.CharField(required=False)
    is_part_of_dgroup = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        coerce=lambda value: value == "True" if isinstance(value, str) else bool(value),
        empty_value=False,
        widget=forms.Select,
    )
    avatar = forms.ImageField(
        required=False,
        help_text="Images only. On phones you can use the camera.",
    )

    class Meta:
        model = User
        fields = (
            "avatar",
            "nickname",
            "email",
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
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields["avatar"].widget = forms.ClearableFileInput(
            attrs={
                "class": TW_FILE,
                "accept": "image/*",
                "capture": "user",
            }
        )
        _configure_avatar_field(self.fields["avatar"])
        social_media_value = self.initial.get("social_media")
        if social_media_value in ({}, "{}", None):
            self.initial["social_media"] = ""
        leaders = (
            User.objects.filter(roles__code=RoleCode.DGROUP_LEADER)
            .distinct()
            .order_by("first_name", "last_name", "email")
        )
        if self.instance and self.instance.pk:
            leaders = leaders.exclude(pk=self.instance.pk)
        self.fields["dgroup_leader"].queryset = leaders
        self.fields["dgroup_leader"].required = False

    def clean_social_media(self):
        value = (self.cleaned_data.get("social_media") or "").strip()
        return "" if value == "{}" else value

    def clean(self):
        cleaned_data = super().clean()
        is_part_of_dgroup = cleaned_data.get("is_part_of_dgroup")
        dgroup_leader = cleaned_data.get("dgroup_leader")
        if is_part_of_dgroup and dgroup_leader and dgroup_leader == self.instance:
            self.add_error("dgroup_leader", "You cannot select yourself as DGroup leader.")
        if not is_part_of_dgroup:
            cleaned_data["dgroup_leader"] = None
        if is_part_of_dgroup and not dgroup_leader:
            self.add_error(
                "dgroup_leader",
                "DGroup leader is required when user is part of a DGroup.",
            )
        if dgroup_leader and is_part_of_dgroup:
            if not dgroup_leader.roles.filter(code=RoleCode.DGROUP_LEADER).exists():
                self.add_error("dgroup_leader", "Selected user must be a DGroup leader.")
        return cleaned_data


class UserProfileUpdateForm(AvatarSaveMixin, StyledFormMixin, forms.ModelForm):
    social_media = forms.CharField(required=False)
    is_part_of_dgroup = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        coerce=lambda value: value == "True" if isinstance(value, str) else bool(value),
        empty_value=False,
        widget=forms.Select,
    )
    avatar = forms.ImageField(
        required=False,
        help_text="Images only. On phones you can use the camera.",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "avatar",
            "nickname",
            "email",
            "mobile_number",
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
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields["avatar"].widget = forms.ClearableFileInput(
            attrs={
                "class": TW_FILE,
                "accept": "image/*",
                "capture": "user",
            }
        )
        _configure_avatar_field(self.fields["avatar"])
        social_media_value = self.initial.get("social_media")
        if social_media_value in ({}, "{}", None):
            self.initial["social_media"] = ""
        leaders = (
            User.objects.filter(roles__code=RoleCode.DGROUP_LEADER)
            .distinct()
            .order_by("first_name", "last_name", "email")
        )
        if self.instance and self.instance.pk:
            leaders = leaders.exclude(pk=self.instance.pk)
        self.fields["dgroup_leader"].queryset = leaders
        self.fields["dgroup_leader"].required = False

    def clean_social_media(self):
        value = (self.cleaned_data.get("social_media") or "").strip()
        return "" if value == "{}" else value

    def clean(self):
        cleaned_data = super().clean()
        is_part_of_dgroup = cleaned_data.get("is_part_of_dgroup")
        dgroup_leader = cleaned_data.get("dgroup_leader")
        if is_part_of_dgroup and dgroup_leader and dgroup_leader == self.instance:
            self.add_error("dgroup_leader", "You cannot select yourself as DGroup leader.")
        if not is_part_of_dgroup:
            cleaned_data["dgroup_leader"] = None
        if is_part_of_dgroup and not dgroup_leader:
            self.add_error(
                "dgroup_leader",
                "DGroup leader is required when user is part of a DGroup.",
            )
        if dgroup_leader and is_part_of_dgroup:
            if not dgroup_leader.roles.filter(code=RoleCode.DGROUP_LEADER).exists():
                self.add_error("dgroup_leader", "Selected user must be a DGroup leader.")
        return cleaned_data


class TailwindPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            field.widget.attrs["class"] = TW_INPUT


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            field.widget.attrs["class"] = TW_INPUT


class AdminUserUpdateForm(AvatarSaveMixin, StyledFormMixin, forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.none(),
        required=False,
        widget=forms.SelectMultiple,
    )
    is_part_of_dgroup = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        coerce=lambda value: value == "True" if isinstance(value, str) else bool(value),
        empty_value=False,
        widget=forms.Select,
    )
    is_profile_completed = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        coerce=lambda value: value == "True" if isinstance(value, str) else bool(value),
        empty_value=False,
        widget=forms.Select,
    )
    is_active = forms.TypedChoiceField(
        label="Status",
        choices=ACTIVE_INACTIVE,
        coerce=lambda value: value == "True" if isinstance(value, str) else bool(value),
        empty_value=True,
        widget=forms.Select,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "avatar",
            "nickname",
            "email",
            "mobile_number",
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
            "roles",
            "is_profile_completed",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields["is_part_of_dgroup"].widget.attrs["class"] = TW_SELECT
        self.fields["is_profile_completed"].widget.attrs["class"] = TW_SELECT
        self.fields["is_active"].widget.attrs["class"] = TW_SELECT
        self.fields["avatar"].widget = forms.ClearableFileInput(
            attrs={"class": TW_FILE, "accept": "image/*"}
        )
        _configure_avatar_field(self.fields["avatar"])
        self.fields["roles"].queryset = Role.objects.filter(is_active=True).order_by(
            "name"
        )
        self.fields["roles"].widget.attrs["class"] = TW_SELECT_MULTI_ROLES
        self.fields["roles"].widget.attrs.setdefault("size", 8)
        self.fields["roles"].help_text = "Use Ctrl/Cmd + click to select multiple roles."
        leaders = (
            User.objects.filter(roles__code=RoleCode.DGROUP_LEADER)
            .distinct()
            .order_by("first_name", "last_name", "email")
        )
        if self.instance and self.instance.pk:
            leaders = leaders.exclude(pk=self.instance.pk)
        self.fields["dgroup_leader"].queryset = leaders
        self.fields["dgroup_leader"].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_part_of_dgroup = cleaned_data.get("is_part_of_dgroup")
        dgroup_leader = cleaned_data.get("dgroup_leader")
        if is_part_of_dgroup and not dgroup_leader:
            self.add_error(
                "dgroup_leader",
                "DGroup leader is required when user is part of a DGroup.",
            )
        if not is_part_of_dgroup:
            cleaned_data["dgroup_leader"] = None
        return cleaned_data


class RoleForm(StyledFormMixin, forms.ModelForm):
    is_active = forms.TypedChoiceField(
        label="Status",
        choices=ACTIVE_INACTIVE,
        coerce=lambda v: v == "True" if isinstance(v, str) else bool(v),
        empty_value=True,
        widget=forms.Select,
    )

    class Meta:
        model = Role
        fields = ("code", "name", "description", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields["is_active"].widget.attrs["class"] = TW_SELECT
        self.fields["code"].help_text = (
            "Short unique code, e.g. WELCOME_TEAM. Stored uppercase."
        )
        self.fields["description"].widget = forms.Textarea(attrs={"rows": 2})
        if self.instance and self.instance.pk:
            self.fields["code"].widget.attrs["readonly"] = True
            self.fields["code"].help_text = "Code is fixed after creation. Create a new role for a new code."

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code:
            raise forms.ValidationError("Code is required.")
        return code.upper().replace(" ", "_")
