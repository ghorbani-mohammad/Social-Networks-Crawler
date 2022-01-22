import asyncio
from telethon import TelegramClient

from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger

from . import models

logger = get_task_logger(__name__)


@shared_task(name="telegram")
def telegram(account_id):
    account = models.Account.objects.get(pk=account_id)
    client = TelegramClient(
        'telegram_sessions/' + account.phone_number,
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
    )

    async def test():
        result = client.connect()
        result = client.is_user_authorized()

    loop = asyncio.get_event_loop()
    task = loop.create_task(test())
    loop.run_until_complete(task)
