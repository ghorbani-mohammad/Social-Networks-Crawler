from rest_framework import serializers

from . import models


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Network
        fields = ("id", "name", "url", "status", "today_posts_count")


class ChannelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["tags"] = TagSerializer(instance.tags.all(), many=True).data
        return data

    class Meta:
        model = models.Channel
        fields = (
            "id",
            "name",
            "username",
            "description",
            "network",
            "tags",
            "status",
            "today_posts_count",
            "created_at",
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ("id", "name", "created_at")


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Post
        fields = (
            "id",
            "body",
            "channel",
            "views_count",
            "share_count",
            "sentiment",
            "ner",
            "category",
            "created_at",
        )


class PostCountInputSerializer(serializers.Serializer):
    type = serializers.CharField()
    date_after = serializers.DateTimeField(required=False, default=None)
    date_before = serializers.DateTimeField(required=False, default=None)


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Keyword
        fields = ("id", "keyword", "created_at")
