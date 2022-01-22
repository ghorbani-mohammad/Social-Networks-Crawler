from rest_framework import serializers

from . import models


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Network
        fields = ("id", "name", "url", "status", "today_posts_count")


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Channel
        fields = (
            "id",
            "username",
            "description",
            "network",
            "status",
            "today_posts_count",
        )
