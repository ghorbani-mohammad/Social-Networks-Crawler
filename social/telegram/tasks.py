from telethon import TelegramClient

from django.conf import settings
from celery.decorators import task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@task(name="telegram")
def telegram():
    client = TelegramClient(settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    print(client)
