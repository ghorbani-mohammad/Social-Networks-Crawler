from django.db import models

from reusable.models import BaseModel


class Keyword(BaseModel):
    name = models.CharField(max_length=20)
    words = models.TextField()

    @property
    def keywords_in_array(self):
        return self.words.split(",")

    def __str__(self):
        return f"({self.pk} - {self.name})"


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
    keywords = models.ManyToManyField(Keyword, blank=True)

    @property
    def keywords_in_array(self):
        result = []
        for keyword in self.keywords.all():
            result = result + keyword.keywords_in_array
        return result

    def __str__(self):
        return f"({self.pk} - {self.name})"


class IgnoredContent(BaseModel):
    url = models.URLField(null=True)
    content = models.TextField(null=True)


class IgnoringFilter(BaseModel):
    LOCATION = "location"
    TITLE = "title"
    PLACE_CHOICES = ((LOCATION, LOCATION), (TITLE, TITLE))
    place = models.CharField(choices=PLACE_CHOICES, max_length=15)

    keyword = models.TextField(null=True)
