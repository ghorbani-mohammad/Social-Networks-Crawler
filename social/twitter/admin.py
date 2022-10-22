from django.contrib import admin

from . import models, tasks
from reusable.admins import ReadOnlyAdminDateFields


@admin.register(models.SearchPage)
class SearchPageAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "enable",
        "last_crawl_at",
    )

    def crawl_page_action(modeladmin, request, queryset):
        for page in queryset:
            tasks.crawl_search_page.delay(page.id)

    actions = [crawl_page_action]
    readonly_fields = ReadOnlyAdminDateFields.readonly_fields + ("last_crawl_at",)
