from django.db import models, transaction

from reusable.models import BaseModel
from twitter import tasks as twi_tasks
from linkedin import tasks as lin_tasks


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

    class Meta:
        unique_together = ('network', 'username')

    @property
    def today_posts_count(self):
        return self.posts.count()

    def __str__(self):
        return f'({self.pk} - {self.name} - {self.network})'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.network.name == 'Linkedin':
                transaction.on_commit(
                    lambda: lin_tasks.get_channel_posts.delay(self.pk)
                )
            elif self.network.name == 'Twitter':
                transaction.on_commit(
                    lambda: twi_tasks.get_twitter_posts.delay(self.pk)
                )


class Post(BaseModel):
    body = models.TextField()
    network_id = models.CharField(max_length=200, null=True, blank=True)
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='posts', null=True
    )
    views_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    data = models.JSONField(null=True)

    def __str__(self):
        return f'({self.pk} - {self.channel})'
