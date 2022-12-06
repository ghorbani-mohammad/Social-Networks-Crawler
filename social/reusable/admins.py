from django.urls import reverse
from django.conf import settings


class ReadOnlyAdminDateFields:
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )


def url_to_edit_object(obj):
    obj_url = reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=[obj.id],
    )
    return f"{settings.BACKEND_URL[:-1]}{obj_url}"
