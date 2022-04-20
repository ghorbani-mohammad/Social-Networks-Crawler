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
        "username",
        "crawl_interval",
        "get_last_crawl",
        "network",
        "status",
        "joined",
        "today_posts_count",
        "created_at",
    )
    list_filter = ("network",)

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
    list_display = ("pk", "channel", "views_count", "share_count", "get_created_at")
    list_filter = ("channel__network",)

    @admin.display(ordering="created_at", description="created_at")
    def get_created_at(self, instance):
        return instance.created_at.astimezone(tz("Asia/Tehran")).strftime(
            "%m/%d %H:%M:%S"
        )


@admin.register(models.Keyword)
class KeywordAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "get_post", "keyword", "get_created_at")
    raw_id_fields = ("post",)

    @admin.display(ordering="created_at", description="created_at")
    def get_created_at(self, instance):
        return instance.created_at.astimezone(tz("Asia/Tehran")).strftime(
            "%m/%d %H:%M:%S"
        )

    @admin.display(ordering="post", description="post")
    def get_post(self, instance):
        return instance.post.admin_link
