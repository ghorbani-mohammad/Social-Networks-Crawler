import json
import asyncio
from telethon import TelegramClient, events, functions
from telethon.tl.functions.channels import GetFullChannelRequest
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
        '/app/telegram_sessions/' + account.phone_number,
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
def update_channel_info(channel_username, info):
    channel = net_models.Channel.objects.get(username=channel_username)
    data = {}
    data['channel_id'] = info.full_chat.id
    data['about'] = info.full_chat.about
    data['participants_count'] = info.full_chat.participants_count
    data['unread_count'] = info.full_chat.unread_count
    channel.data = data
    channel.save()


def get_message_statics_info(account_id, channel_username, message_ids):
    account, client = get_account_client(account_id)
    client.start()

    async def main():
        result = await client(
            functions.messages.GetMessagesViewsRequest(
                peer=channel_username, id=message_ids, increment=False
            )
        )
        for index, item in enumerate(result.views):
            await update_message_info(
                channel_username, message_ids[index], item.views, item.forwards
            )

    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.run_until_complete(task)
    client.disconnect()


@sync_to_async
def set_channels_list_async():
    channels = [channel.username for channel in net_models.Channel.objects.all()]
    if len(channels):
        cache.set('telegram_channels', json.dumps(channels))


@sync_to_async
def insert_to_db(channel_username, event):
    # todo: use cache for getting channel
    channel = net_models.Channel.objects.get(username=channel_username)
    message_id = event.message.id
    channel_id = event.message.peer_id.channel_id
    text = event.message.message
    data = {'message_id': message_id, 'channel_id': channel_id}
    net_models.Post.objects.create(body=text, channel=channel, data=data)


@sync_to_async
def update_message_info(channel_username, message_id, views_count, forwards_count):
    channel = net_models.Channel.objects.get(username=channel_username)
    post = net_models.Post.objects.get(channel=channel, data__message_id=message_id)
    post.views_count = views_count or 0
    post.share_count = forwards_count or 0
    post.save()


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
    client.disconnect()


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
    client.disconnect()


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
            await insert_to_db(sender.username, event)

    client.run_until_disconnected()
    client.disconnect()


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


@shared_task(name="get_channel_info")
def get_channel_info(account_id, channel_username):
    _, client = get_account_client(account_id)

    async def main():
        await client.connect()
        channel = await client.get_entity(channel_username)
        info = await client(GetFullChannelRequest(channel=channel))
        await update_channel_info(channel_username, info)

    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.run_until_complete(task)
    client.disconnect()


@shared_task(name="update_message_statics")
def update_message_statics():
    channels = net_models.Channel.objects.filter(network__name='Telegram')
    for channel in channels:
        posts = channel.posts.filter(views_count=0).order_by('-created_at')
        # post_ids = post.values_list('id')
        post_ids_array = []
        for post in posts:
            if post.data and 'message_id' in post.data:
                post_ids_array.append(post.data['message_id'])
        print(channel.username)
        print(post_ids_array)
