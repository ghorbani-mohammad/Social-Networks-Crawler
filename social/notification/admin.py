from django.contrib import admin

from reusable.admins import ReadOnlyAdminDateFieldsMIXIN
from . import models


@admin.register(models.TelegramBot)
class TelegramBotAdmin(ReadOnlyAdminDateFieldsMIXIN, admin.ModelAdmin):
    list_display = ("pk", "name", "created_at")


@admin.register(models.TelegramAccount)
class TelegramAccountAdmin(ReadOnlyAdminDateFieldsMIXIN):
    list_display = ("pk", "name", "chat_id", "created_at")


@admin.register(models.Channel)
class ChannelAdmin(ReadOnlyAdminDateFieldsMIXIN):
    list_display = ("pk", "name", "username", "network", "created_at")
