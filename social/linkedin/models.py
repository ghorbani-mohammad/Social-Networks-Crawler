from django.db import models

from reusable.models import BaseModel


class JobPage(BaseModel):
    url = models.URLField()
    name = models.CharField(max_length=100)
    enable = models.BooleanField(default=True)
