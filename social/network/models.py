from django.db import models

from reusable.models import BaseModel


class Network(BaseModel):
    name = models.CharField(max_length=100)
    url = models.URLField()
    status = models.BooleanField(default=True)

    @property
    def today_posts_count(self):
        return 10

    def __str__(self):
        return f'({self.pk} - {self.name})'


class Channel(BaseModel):
    username = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    network = models.ForeignKey(Network, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)

    class Meta:
        unique_together = ('network', 'username')

    @property
    def today_posts_count(self):
        return 10

    def __str__(self):
        return f'({self.pk} - {self.username} - {self.network})'


class Post(BaseModel):
    body = models.TextField(max_length=100)
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name='posts', null=True
    )
    views_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    def __str__(self):
        return f'({self.pk} - {self.channel})'
