from django.db import models, transaction

from user.models import Profile
from reusable.models import BaseModel
from . import tasks


class CoverLetter(BaseModel):
    cover_letter = models.TextField(null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="cover_letter",
    )

    def save(self, *args, **kwargs):
        created = bool(self.pk)
        with transaction.atomic():
            if created:
                transaction.on_commit(lambda: tasks.create_cover_letter.delay(self.pk))
            super().save(*args, **kwargs)
