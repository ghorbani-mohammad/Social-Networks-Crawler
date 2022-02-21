from pytz import timezone as tz

from django.contrib import admin
from reusable.admins import ReadOnlyAdminDateFields

from . import models


@admin.register(models.Network)
class NetworkAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "url",
        "status",
        "today_posts_count",
        "today_posts_count",
    )


@admin.register(models.Channel)
class ChannelAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "username",
        "network",
        "status",
        "joined",
        "today_posts_count",
        "created_at",
    )
    list_filter = ("network",)


@admin.register(models.Post)
class PostAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "channel", "views_count", "share_count", "get_created_at")
    list_filter = ("channel__network",)

    @admin.display(ordering="created_at", description="created_at")
    def get_created_at(self, instance):
        return instance.created_at.astimezone(tz('Asia/Tehran')).strftime(
            "%m/%d %H:%M:%S"
        )


@admin.register(models.Keyword)
class KeywordAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "post", "keyword", "get_created_at")
    raw_id_fields = ("post",)

    @admin.display(ordering="created_at", description="created_at")
    def get_created_at(self, instance):
        return instance.created_at.astimezone(tz('Asia/Tehran')).strftime(
            "%m/%d %H:%M:%S"
        )

    @admin.display(ordering="post", description="post")
    def get_post(self, instance):
        return instance.post.admin_link
