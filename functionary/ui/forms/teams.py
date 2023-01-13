from django.forms import ChoiceField, ModelChoiceField, ModelForm

from core.models import TeamUserRole, User
from core.models.user_role import ROLE_CHOICES


class TeamUserRoleForm(ModelForm):
    role = ChoiceField(choices=ROLE_CHOICES, required=True)
    user = ModelChoiceField(
        queryset=User.objects.all(),
        to_field_name="username",
        required=True,
        error_messages={
            "required": "User does not exist.",
            "invalid_choice": "User does not exist.",
        },
    )

    class Meta:
        model = TeamUserRole
        fields = "__all__"
