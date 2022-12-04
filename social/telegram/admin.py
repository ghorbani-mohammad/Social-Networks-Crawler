from django.contrib import admin

from . import models
from reusable.admins import ReadOnlyAdminDateFields


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("pk", "created_at", "phone_number", "phone_code_hash")
    readonly_fields = ReadOnlyAdminDateFields.readonly_fields + ("phone_code_hash",)
