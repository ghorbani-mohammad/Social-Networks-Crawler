import json
import asyncio
from telethon import TelegramClient, events
from asgiref.sync import sync_to_async

from django.conf import settings
from django.core.cache import cache
from celery import shared_task
from celery.utils.log import get_task_logger

from . import models
from network import models as net_models

logger = get_task_logger(__name__)


def get_account_client(account_id):
    account = models.Account.objects.get(pk=account_id)
    client = TelegramClient(
        'telegram_sessions/' + account.phone_number,
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
    )
    return account, client


@sync_to_async
def save_phone_code_hash(account_id, hash_code):
    account = models.Account.objects.get(pk=account_id)
    account.phone_code_hash = hash_code
    account.save()


@sync_to_async
def set_channels_list_async():
    channels = [channel.username for channel in net_models.Channel.objects.all()]
    if len(channels):
        cache.set('telegram_channels', json.dumps(channels))


@sync_to_async
def insert_to_db(channel_username, text):
    # todo: use cache
    channel = net_models.Channel.objects.get(username=channel_username)
    net_models.Post.objects.create(body=text, channel=channel)


@shared_task(name="get_code")
def get_code(account_id):
    account, client = get_account_client(account_id)

    async def main():
        await client.connect()
        await client.is_user_authorized()
        result = await client.send_code_request(account.phone_number)
        await save_phone_code_hash(account_id, result.phone_code_hash)

    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.run_until_complete(task)


@shared_task(name="sign_in")
def sign_in(account_id, code):
    account, client = get_account_client(account_id)

    async def main():
        await client.connect()
        myself = await client.sign_in(
            account.phone_number,
            code,
            phone_code_hash=account.phone_code_hash,
        )

    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.run_until_complete(task)


@shared_task(name="get_messages")
def get_messages(account_id):
    _, client = get_account_client(account_id)
    client.start()

    @client.on(events.NewMessage(incoming=True))
    async def my_event_handler(event):
        sender = await event.get_sender()
        await set_channels_list_async()
        channels = get_channels_list()
        if sender.username in channels:
            await insert_to_db(sender.username, event.raw_text)

    client.run_until_disconnected()


@shared_task(name="set_channels_list")
def set_channels_list():
    channels = [channel.username for channel in net_models.Channel.objects.all()]
    if len(channels):
        cache.set('telegram_channels', json.dumps(channels))


@shared_task(name="get_channels_list")
def get_channels_list():
    channels = cache.get('telegram_channels')
    if channels:
        return json.loads(channels)
    return []
