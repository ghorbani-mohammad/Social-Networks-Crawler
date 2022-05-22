from celery import shared_task

from . import models, utils


@shared_task()
def count_daily_news(message):
    bot = models.TelegramBot.objects.first()
    account = models.TelegramAccount.objects.first()
    utils.telegram_bot_sendtext(bot.telegram_token, account.chat_id, message)
