import requests

from django.db import transaction
from django.utils import timezone
from celery import Task
from celery import shared_task
from celery.utils.log import get_task_logger

from . import models
from twitter import tasks as twi_tasks
from linkedin import tasks as lin_tasks

logger = get_task_logger(__name__)

NER_KEY_MAPPING = {
    "date": "تاریخ",
    "time": "زمان",
    "event": "رویداد",
    "money": "مالی",
    "person": "شخص",
    "percent": "درصد",
    "product": "محصول",
    "facility": "تسهیلات",
    "location": "مکان",
    "organization": "سازمان",
}


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 10}
    retry_backoff = 5
    default_retry_delay = 60
    retry_jitter = True


@shared_task(base=BaseTaskWithRetry)
def extract_keywords(post_id):
    post = models.Post.objects.get(id=post_id)
    resp = requests.post(
        "http://analyzer_api/api/v1/keword_extraction/", {"body": post.body}
    ).json()
    objs = []
    for keyword in resp["keywords"]:
        objs.append(models.Keyword(post=post, keyword=keyword))
    models.Keyword.objects.bulk_create(objs)


@shared_task(base=BaseTaskWithRetry)
def extract_ner(post_id):
    with transaction.atomic():
        post = models.Post.objects.select_for_update().get(id=post_id)
        resp = requests.post(
            "http://persian_analyzer_api/v1/app/ner/", {"text": post.body}
        ).json()
        temp = {}
        for key in NER_KEY_MAPPING.keys():
            temp[NER_KEY_MAPPING[key]] = resp.pop(key)
        post.ner = temp
        post.save()


@shared_task(base=BaseTaskWithRetry)
def extract_sentiment(post_id):
    with transaction.atomic():
        post = models.Post.objects.select_for_update().get(id=post_id)
        resp = requests.post(
            "http://persian_analyzer_api/v1/app/sentiment/", {"text": post.body}
        ).json()
        post.sentiment = resp
        post.save()


@shared_task(base=BaseTaskWithRetry)
def extract_categories(post_id):
    with transaction.atomic():
        post = models.Post.objects.select_for_update().get(id=post_id)
        resp = requests.post(
            "http://persian_analyzer_api/v1/app/classification/", {"text": post.body}
        ).json()
        post.category = resp
        post.save()


@shared_task()
def check_channels_crawl():
    channels = models.Channel.objects.filter(last_crawl__isnull=False)
    for channel in channels:
        interval = timezone.localtime() - channel.last_crawl
        hours = interval.total_seconds() / 3600
        if hours >= channel.crawl_interval:
            print(f"******* channel {channel} must crawled")
            if channel.network.name == "Twitter":
                twi_tasks.get_twitter_posts(channel.pk)
            elif channel.network.name == "LinkedIn":
                lin_tasks.get_linkedin_posts(channel.pk)
