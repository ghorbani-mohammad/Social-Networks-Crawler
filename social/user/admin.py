from django.contrib import admin

from . import models
from reusable.admins import ReadOnlyAdminDateFieldsMIXIN


@admin.register(models.Profile)
class ProfileAdmin(ReadOnlyAdminDateFieldsMIXIN):
    list_display = ("pk", "user", "cell_number", "chat_id")
