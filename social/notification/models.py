from django.db import models

from reusable.models import BaseModel


class TelegramBot(BaseModel):
    """Bots which we use to send messages to specified channels"""

    name = models.CharField(max_length=50)
    telegram_token = models.CharField(max_length=100)

    def __str__(self):
        return f"({self.pk} - {self.name})"


class TelegramAccount(BaseModel):
    """
    Telegram accounts which we send mainly monitoring messages.
    For example how many new links we have seen today.
    """

    name = models.CharField(max_length=50)
    chat_id = models.CharField(max_length=100)

    def __str__(self):
        return f"({self.pk} - {self.name})"


class Channel(BaseModel):
    """We defined channels for publish our crawled data

    Args:
        BaseModel (Model): base model with created_at, updated_at and deleted_at fields
    """

    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    network = models.ForeignKey(
        "network.Network",
        on_delete=models.CASCADE,
        related_name="notification_channels",
    )

    def __str__(self):
        return f"({self.pk} - {self.name})"
