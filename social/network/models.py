from django.db import models, transaction

from reusable.models import BaseModel
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
        return f'({self.pk} - {self.username} - {self.network})'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.network.name == 'Linkedin':
                transaction.on_commit(lambda: lin_tasks.get_company_info.delay(self.pk))


class Post(BaseModel):
    body = models.TextField(max_length=100)
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='posts', null=True
    )
    views_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    data = models.JSONField(null=True)

    def __str__(self):
        return f'({self.pk} - {self.channel})'
