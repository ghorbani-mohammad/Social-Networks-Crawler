from django.contrib import admin

from . import models
from reusable.admins import ReadOnlyAdminDateFieldsMIXIN


@admin.register(models.CoverLetter)
class CoverLetterAdmin(ReadOnlyAdminDateFieldsMIXIN):
    list_display = ("pk", "profile", "created_at")
    readonly_fields = ("cover_letter",)
