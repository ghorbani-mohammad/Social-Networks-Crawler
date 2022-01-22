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


class Publisher(BaseModel):
    username = models.CharField(max_length=100)
    network = models.ForeignKey(Network, on_delete=models.CASCADE)
    is_channel = models.BooleanField(default=False)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f'({self.pk} - {self.username})'


class Post(BaseModel):
    body = models.CharField(max_length=100)
    publisher = models.ForeignKey(
        Publisher, on_delete=models.CASCADE, related_name='posts', null=True
    )
    views_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    def __str__(self):
        return f'({self.pk} - {self.publisher})'
