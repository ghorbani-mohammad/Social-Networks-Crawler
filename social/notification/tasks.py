from celery import shared_task

from . import models, utils
from network.models import OutputChannel


@shared_task()
def send_telegram_message(message):
    """This function gets a string message and sends it to all defined accounts.

    Args:
        message (str): text message

    Raises:
        Exception: if sending message was not successful.
    """
    bot = models.TelegramBot.objects.last()
    accounts = models.TelegramAccount.objects.all()
    for account in accounts:
        resp = utils.telegram_bot_sendtext(bot.telegram_token, account.chat_id, message)
        if not resp["ok"]:
            raise Exception(resp["description"])


@shared_task()
def send_message_to_telegram_channel(message, channel_pk):
    """This function gets a string message and sends it to specific channel.

    Args:
        message (str): text message
        channel_pk (int): id of destination channel (OutputChannel)

    Raises:
        Exception: if sending message was not successful.
    """
    bot = models.TelegramBot.objects.last()
    channel_output = OutputChannel.objects.get(pk=channel_pk)
    resp = utils.telegram_bot_sendtext(
        bot.telegram_token, channel_output.username, message
    )
    if not resp["ok"]:
        raise Exception(resp["description"])
