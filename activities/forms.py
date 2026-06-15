from django import forms
from accounts.field_themes import TW_INPUT, TW_TEXTAREA

from .models import Activity


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["name", "description", "date", "location"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TW_INPUT}),
            "date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": TW_INPUT},
            ),
            "location": forms.TextInput(attrs={"class": TW_INPUT}),
            "description": forms.Textarea(attrs={"class": TW_TEXTAREA, "rows": 4}),
        }
