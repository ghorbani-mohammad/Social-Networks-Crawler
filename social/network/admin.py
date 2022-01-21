from django.contrib import admin
from reusable.admins import ReadOnlyAdminDateFields

from . import models


@admin.register(models.Network)
class NetworkAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "name", "url", "status")


@admin.register(models.Publisher)
class PublisherAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "username", "network", "is_channel", "status", "created_at")


@admin.register(models.Post)
class PostAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "publisher", "views_count", "share_count", "created_at")