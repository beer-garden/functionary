""" TeamMember model """
from django.conf import settings
from django.db import models


class TeamMember(models.Model):
    """Tracks what users are on which teams and their roles

    Attributes:
        user: Foreign key to User
        team: Foreign key to Team
        role: The user's role on the team
    """

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        db_index=True,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    team = models.ForeignKey(
        to="Team", db_index=True, on_delete=models.CASCADE, related_name="members"
    )

    # TODO: Placeholder for demo purposes
    role = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.team.name} - {self.user.username} - {self.role}"
