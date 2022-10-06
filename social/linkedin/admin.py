from django.contrib import admin

from . import models, tasks
from reusable.admins import ReadOnlyAdminDateFields


@admin.register(models.JobPage)
class JobPageAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "enable",
        "last_crawl_at",
    )

    def crawl_page_action(modeladmin, request, queryset):
        for page in queryset:
            tasks.get_job_page_posts.delay(page.id)

    actions = [crawl_page_action]
