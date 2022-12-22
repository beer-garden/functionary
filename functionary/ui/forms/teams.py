from django.forms import ChoiceField, Form, ModelChoiceField

from core.auth import Role
from core.models import Team, User

ROLE_CHOICES = [(role.name, role.value) for role in Role]


class TeamUserRoleForm(Form):
    team = ModelChoiceField(queryset=Team.objects.all(), required=True)
    user = ModelChoiceField(queryset=User.objects.all(), required=True)
    role = ChoiceField(choices=ROLE_CHOICES, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
