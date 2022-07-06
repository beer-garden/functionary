""" Package serializers """
from rest_framework import serializers

from core.models import Package


class PackageSerializer(serializers.ModelSerializer):
    """Basic serializer for the Package model"""

    class Meta:
        model = Package
        fields = "__all__"
