from django.contrib import admin

from . import models
from reusable.admins import ReadOnlyAdminDateFields


@admin.register(models.TelegramBot)
class TelegramBotAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "name", "created_at")


@admin.register(models.TelegramAccount)
class TelegramAccountAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "chat_id",
        "created_at",
    )
