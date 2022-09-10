from django.db import models

from reusable.models import BaseModel


class Account(BaseModel):
    phone_number = models.CharField(max_length=15)
    phone_code_hash = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"({self.pk} - {self.phone_number})"
