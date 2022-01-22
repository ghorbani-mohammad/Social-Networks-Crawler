from rest_framework import serializers

from . import models


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Network
        fields = ("id", "name", "url", "status", "today_posts_count")


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Publisher
        fields = (
            "id",
            "username",
            "network",
            "is_channel",
            "status",
            "today_posts_count",
        )
