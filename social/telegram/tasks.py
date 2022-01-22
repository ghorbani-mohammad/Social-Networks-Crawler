import asyncio
from telethon import TelegramClient

from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger

from . import models

logger = get_task_logger(__name__)


@shared_task(name="get_code")
def get_code(account_id):
    account = models.Account.objects.get(pk=account_id)
    client = TelegramClient(
        'telegram_sessions/' + account.phone_number,
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
    )

    async def main():
        await client.connect()
        await client.is_user_authorized()
        await client.send_code_request(account.phone_number)

    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.run_until_complete(task)
