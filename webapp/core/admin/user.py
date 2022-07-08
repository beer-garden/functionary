""" Admin panel overrides for User model """
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from core.models import User


class UserAdminCreationForm(forms.ModelForm):
    """Form for Creating User instances."""

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        exclude = ()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                "The passwords do not match!", code="password_mismatch"
            )

        return password2

    def save(self, commit=True):
        """Save function override to ensure password is hashed properly"""
        user = super().save(commit=False)

        # set user password and save
        password2 = self.cleaned_data.get("password2")
        user.set_password(password2)

        if commit:
            user.save()

        return user


class UserAdminChangeForm(UserChangeForm):
    """Form for updating user instances."""

    class Meta:
        model = User
        exclude = ()

    def __init__(self, *args, **kwargs):
        """Override constructor to disable non-editable fields"""
        super().__init__(*args, **kwargs)

        password = self.fields.get("password")
        if password:
            password.help_text = password.help_text.format("../password/")


class UserAdmin(BaseUserAdmin):
    """Admin override for the User model"""

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    readonly_fields = [
        "created_at",
        "last_login",
    ]

    _personal_info = (
        "Personal Info",
        {
            "fields": (
                "first_name",
                "last_name",
            )
        },
    )
    _permissions = (
        "Permissions",
        {
            "fields": ("is_active", "is_staff", "is_superuser"),
        },
    )
    _important_dates = ("Important dates", {"fields": ("last_login", "created_at")})

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "password",
                )
            },
        ),
        _personal_info,
        _permissions,
        _important_dates,
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "password1",
                    "password2",
                ),
            },
        ),
        _personal_info,
        _permissions,
    )
    list_filter = ("is_staff", "is_superuser", "is_active")
    filter_horizontal = ()
