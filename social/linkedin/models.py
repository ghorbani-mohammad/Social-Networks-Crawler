from django.db import models

from reusable.models import BaseModel


class Keyword(BaseModel):
    name = models.CharField(max_length=20)
    words = models.TextField()


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
    keywords = models.ManyToManyField(Keyword)

    def __str__(self):
        return f"({self.pk} - {self.name})"


class IgnoredContent(BaseModel):
    url = models.URLField(null=True)
    content = models.TextField(null=True)
