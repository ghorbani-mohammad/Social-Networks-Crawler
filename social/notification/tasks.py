from celery import shared_task

from . import models, utils


@shared_task()
def send_telegram_message(message):
    bot = models.TelegramBot.objects.first()
    account = models.TelegramAccount.objects.first()
    return utils.telegram_bot_sendtext(bot.telegram_token, account.chat_id, message)
