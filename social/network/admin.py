import redis
from pytz import timezone as tz

from django.contrib import admin
from reusable.admins import ReadOnlyAdminDateFields

from . import models
from twitter import tasks as twi_tasks
from linkedin import tasks as lin_tasks


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
        "network",
        "username",
        "language",
        "crawl_interval",
        "get_last_crawl",
        "status",
        "joined",
        "today_posts_count",
        "created_at",
    )
    list_filter = (
        "network",
        "language",
    )

    @admin.display(ordering="last_crawl", description="last_crawl")
    def get_last_crawl(self, instance):
        if instance.last_crawl:
            return instance.last_crawl.astimezone(tz("Asia/Tehran")).strftime(
                "%m/%d %H:%M:%S"
            )

    def crawl(self, request, queryset):
        for channel in queryset:
            if channel.network.name == "Twitter":
                twi_tasks.get_twitter_posts.delay(channel.pk)
            elif channel.network.name == "Linkedin":
                lin_tasks.get_linkedin_posts.delay(channel.pk)

    actions = [crawl]


@admin.register(models.Post)
class PostAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = (
        "pk",
        "channel",
        "short_body",
        "views_count",
        "share_count",
        "get_created_at",
    )
    list_filter = ("channel__network",)

    @admin.display(ordering="created_at", description="created_at")
    def get_created_at(self, instance):
        return instance.created_at.astimezone(tz("Asia/Tehran")).strftime(
            "%m/%d %H:%M:%S"
        )


@admin.register(models.Keyword)
class KeywordAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "keyword", "ignored", "get_post", "get_created_at")
    raw_id_fields = ("post",)

    @admin.display(ordering="created_at", description="created_at")
    def get_created_at(self, instance):
        return instance.created_at.astimezone(tz("Asia/Tehran")).strftime(
            "%m/%d %H:%M:%S"
        )

    @admin.display(ordering="post", description="post")
    def get_post(self, instance):
        return instance.post.admin_link


@admin.register(models.Backup)
class BackupAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "link", "status", "type", "get_created_at", "get_updated_at")

    @admin.display(ordering="created_at", description="created_at")
    def get_created_at(self, instance):
        return instance.created_at.astimezone(tz("Asia/Tehran")).strftime(
            "%m/%d %H:%M:%S"
        )

    @admin.display(ordering="updated_at", description="updated_at")
    def get_updated_at(self, instance):
        return instance.updated_at.astimezone(tz("Asia/Tehran")).strftime(
            "%m/%d %H:%M:%S"
        )


@admin.register(models.Config)
class ConfigAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "crawl_linkedin_feed")

    def flush_views_cache(self, request, queryset):
        redis_db = redis.StrictRedis(host="social_redis", port=6379, db=15)
        redis_db.flushdb()

    actions = [flush_views_cache]


@admin.register(models.ChannelListExport)
class ChannelListExportAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = (
        "pk",
        "file",
        "created_at",
    )


@admin.register(models.IgnoredKeyword)
class IgnoredKeywordAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "keyword", "created_at")


@admin.register(models.BlockedKeyword)
class BlockedKeywordAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "keyword", "created_at")
