from django.db import models

from reusable.models import BaseModel


class JobPage(BaseModel):
    url = models.URLField()
    name = models.CharField(max_length=100)
    enable = models.BooleanField(default=True)
    message = models.TextField(null=True, blank=True)
    last_crawl_at = models.DateTimeField(null=True, blank=True)
    output_channel = models.ForeignKey(
        "notification.Channel",
        on_delete=models.SET_NULL,
        null=True,
        related_name="linkedin_pages",
    )

    def __str__(self):
        return f"({self.pk} - {self.name})"
