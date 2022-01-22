from telethon import TelegramClient

from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name="telegram")
def telegram():
    client = TelegramClient(settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    print(client)
