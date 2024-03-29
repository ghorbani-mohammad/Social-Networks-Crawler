from rest_framework import serializers

from . import models


class NetworkShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Network
        fields = ("id", "name", "url", "status")


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Network
        fields = ("id", "name", "url", "status", "today_posts_count")


class ChannelShortSerializer(serializers.ModelSerializer):
    network = NetworkShortSerializer()

    class Meta:
        model = models.Channel
        fields = (
            "id",
            "name",
            "username",
            "description",
            "network",
            "status",
        )


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
            "language",
            "today_posts_count",
            "last_crawl",
            "crawl_interval",
            "created_at",
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ("id", "name", "created_at")


class PostSerializer(serializers.ModelSerializer):
    channel = ChannelShortSerializer()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["category"] = instance.category
        data["sentiment"] = instance.sorted_sentiment
        data["keywords"] = [item.keyword for item in instance.keywords.all()]
        data["channel_name"] = instance.channel.name
        data["channel_language"] = instance.channel.language
        data["network_name"] = instance.channel.network.name
        return data

    class Meta:
        model = models.Post
        fields = (
            "id",
            "body",
            "channel",
            "views_count",
            "share_count",
            "ner",
            "created_at",
        )


class PostCountInputSerializer(serializers.Serializer):
    type = serializers.CharField()
    date_after = serializers.DateTimeField(required=False, default=None)
    date_before = serializers.DateTimeField(required=False, default=None)
    operator = serializers.CharField(required=False, default="or")

    def update(self, _instance, _validated_data):
        pass

    def create(self, _validated_data):
        pass


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Keyword
        fields = ("id", "keyword", "created_at")


class BackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Backup
        fields = (
            "id",
            "link",
            "type",
            "status",
            "created_at",
            "updated_at",
        )
