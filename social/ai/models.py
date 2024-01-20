from django.db import models

from user.models import Profile
from reusable.models import BaseModel


class CoverLetter(BaseModel):
    cover_letter = models.TextField(null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="cover_letter",
    )
