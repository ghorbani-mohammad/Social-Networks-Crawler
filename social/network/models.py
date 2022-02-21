from django.utils import timezone
from django.utils.html import format_html
from django.db import models, transaction

from . import tasks
from reusable.models import BaseModel
from twitter import tasks as twi_tasks
from linkedin import tasks as lin_tasks
from reusable.admins import url_to_edit_object


class Network(BaseModel):
    name = models.CharField(max_length=100)
    url = models.URLField()
    status = models.BooleanField(default=True)

    @property
    def today_posts_count(self):
        counter = 0
        for channel in self.channels.all():
            counter += channel.posts.count()
        return counter

    def __str__(self):
        return f'({self.pk} - {self.name})'


class Channel(BaseModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    network = models.ForeignKey(
        Network, on_delete=models.CASCADE, related_name='channels'
    )
    status = models.BooleanField(default=True)
    data = models.JSONField(null=True, blank=True)
    joined = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ('network', 'username')

    @property
    def today_posts_count(self):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.posts.filter(created_at__gte=today).count()

    def __str__(self):
        return f'({self.pk} - {self.name} - {self.network})'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.network.name == 'Linkedin':
                transaction.on_commit(
                    lambda: lin_tasks.get_channel_posts.delay(self.pk)
                )
            elif self.network.name == 'Twitter':
                transaction.on_commit(
                    lambda: twi_tasks.get_twitter_posts.delay(self.pk)
                )
            elif self.network.name == 'Telegram':
                self.username = self.username.replace('https://t.me/', '')
            super().save(*args, **kwargs)


class Post(BaseModel):
    body = models.TextField()
    network_id = models.CharField(max_length=200, null=True, blank=True)
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='posts', null=True
    )
    views_count = models.IntegerField(null=True, blank=True)
    share_count = models.IntegerField(null=True, blank=True)
    data = models.JSONField(null=True)

    @property
    def admin_link(self):
        url = url_to_edit_object(self)
        return format_html("<a href='{url}'>{stream}</a>", url=url, stream=self)

    def __str__(self):
        return f'({self.pk} - {self.channel})'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            transaction.on_commit(lambda: tasks.extract_keywords.delay(self.pk))


class Keyword(BaseModel):
    post = models.ForeignKey(
        Post,
        related_name="keywords",
        related_query_name="keyword",
        on_delete=models.CASCADE,
    )
    keyword = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"({self.pk} - {self.keyword})"
