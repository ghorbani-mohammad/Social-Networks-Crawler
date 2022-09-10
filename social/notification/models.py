from django.db import models

from reusable.models import BaseModel


class TelegramBot(BaseModel):
    name = models.CharField(max_length=50)
    telegram_token = models.CharField(max_length=100)


class TelegramAccount(BaseModel):
    name = models.CharField(max_length=50)
    chat_id = models.CharField(max_length=100)
