from django.contrib import admin

from . import models, tasks
from reusable.admins import ReadOnlyAdminDateFields


@admin.register(models.JobPage)
class JobPageAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "enable", "output_channel", "last_crawl_at")

    def crawl_page_action(modeladmin, request, queryset):
        for page in queryset:
            tasks.get_job_page_posts.delay(
                page.message, page.url, page.output_channel.pk
            )

    actions = [crawl_page_action]
    readonly_fields = ReadOnlyAdminDateFields.readonly_fields + ("last_crawl_at",)


@admin.register(models.IgnoredContent)
class IgnoredContentAdmin(admin.ModelAdmin):
    list_display = ("pk", "url", "created_at")
