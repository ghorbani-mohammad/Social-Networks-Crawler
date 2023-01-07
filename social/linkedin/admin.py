from django.contrib import admin

from . import models, tasks
from django.utils.html import format_html
from reusable.admins import ReadOnlyAdminDateFields, ReadOnlyAdminDateFieldsMIXIN


@admin.register(models.JobPage)
class JobPageAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "page_link",
        "enable",
        "output_channel",
        "last_crawl_at",
    )

    def page_link(self, obj):
        return format_html("<a href='{url}'>Link</a>", url=obj.url)

    def crawl_page_action(modeladmin, request, queryset):
        for page in queryset:
            tasks.get_job_page_posts.delay(page.pk)

    def crawl_page_repetitive_action(modeladmin, request, queryset):
        for page in queryset:
            tasks.get_job_page_posts.delay(page.pk, ignore_repetitive=False)

    actions = (crawl_page_action, crawl_page_repetitive_action)
    readonly_fields = ReadOnlyAdminDateFields.readonly_fields + ("last_crawl_at",)


@admin.register(models.IgnoredJob)
class IgnoredJobAdmin(ReadOnlyAdminDateFieldsMIXIN, admin.ModelAdmin):
    list_display = ("pk", "url", "created_at")


@admin.register(models.Keyword)
class KeywordAdmin(ReadOnlyAdminDateFieldsMIXIN, admin.ModelAdmin):
    list_display = ("pk", "name", "created_at")


@admin.register(models.IgnoringFilter)
class IgnoringFilterAdmin(ReadOnlyAdminDateFieldsMIXIN, admin.ModelAdmin):
    list_display = ("pk", "place", "keyword", "created_at")
