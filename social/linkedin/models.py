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


class IgnoringFilter(BaseModel):
    TITLE = "title"
    COMPANY = "company"
    LOCATION = "location"
    PLACE_CHOICES = ((LOCATION, LOCATION), (TITLE, TITLE), (COMPANY, COMPANY))
    place = models.CharField(choices=PLACE_CHOICES, max_length=15)
    keyword = models.TextField(null=True)

    def __str__(self):
        return f"({self.pk} - {self.place} - {self.keyword})"


class JobSearch(BaseModel):
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
    ignore_filters = models.ManyToManyField(IgnoringFilter, blank=True)
    page_count = models.PositiveSmallIntegerField(
        help_text="how many pages should be crawled", default=1, blank=True
    )
    priority = models.PositiveSmallIntegerField(
        help_text="pages with higher priority, will be at the first of crawl queue",
        blank=True,
        default=0,
    )

    @property
    def keywords_in_array(self):
        result = []
        for keyword in self.keywords.all():
            result = result + keyword.keywords_in_array
        return result

    @property
    def page_data(self):
        return (
            self.message,
            self.url,
            self.output_channel.pk,
            self.keywords_in_array,
            self.ignore_filters.all(),
        )

    def __str__(self):
        return f"({self.pk} - {self.name})"


class IgnoredJob(BaseModel):
    url = models.URLField(null=True)
    description = models.TextField(null=True)
    title = models.CharField(max_length=150, null=True)
    company = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=200, null=True)
    language = models.CharField(max_length=40, null=True)


class ExpressionSearch(BaseModel):
    url = models.URLField()
    name = models.CharField(max_length=100)
    enable = models.BooleanField(default=True)
    last_crawl_at = models.DateTimeField(null=True, blank=True)
    output_channel = models.ForeignKey(
        "notification.Channel",
        on_delete=models.SET_NULL,
        null=True,
        related_name="linkedin_expression_searches",
    )
