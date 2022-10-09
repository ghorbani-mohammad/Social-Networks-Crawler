from celery import shared_task

from . import models, utils


@shared_task()
def send_telegram_message(message):
    bot = models.TelegramBot.objects.last()
    accounts = models.TelegramAccount.objects.all()
    for account in accounts:
        resp = utils.telegram_bot_sendtext(bot.telegram_token, account.chat_id, message)
        if not resp["ok"]:
            raise Exception(resp["description"])
