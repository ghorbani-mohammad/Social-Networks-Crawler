from django.contrib import admin

from . import models
from reusable.admins import ReadOnlyAdminDateFields


@admin.register(models.Account)
class AccountAdmin(ReadOnlyAdminDateFields, admin.ModelAdmin):
    list_display = ("pk", "phone_number", "created_at")
