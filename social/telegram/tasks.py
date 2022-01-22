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
        account.phone_number, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
    )
    print(client)

    async def test():
        result = client.connect()
        print(result)

    asyncio.run(test())
    asyncio.run(print(client.is_user_authorized()))
