""" User serializers """
from rest_framework import serializers

from core.models import User


class UserSerializer(serializers.ModelSerializer):
    """Basic serializer for the User model"""

    class Meta:
        model = User
        exclude = ["password"]
