import requests

from celery import Task
from celery import shared_task
from celery.utils.log import get_task_logger

from . import models

logger = get_task_logger(__name__)


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
    for keyword in resp['keywords']:
        objs.append(models.Keyword(post=post, keyword=keyword))
    models.Keyword.objects.bulk_create(objs)


@shared_task(base=BaseTaskWithRetry)
def extract_ner(post_id):
    post = models.Post.objects.get(id=post_id)
    resp = requests.post(
        "http://persian_analyzer_api/v1/app/ner/", {"text": post.body}
    ).json()
    post.ner = resp
    post.save()


@shared_task(base=BaseTaskWithRetry)
def extract_sentiment(post_id):
    post = models.Post.objects.get(id=post_id)
    resp = requests.post(
        "http://persian_analyzer_api/v1/app/sentiment/", {"text": post.body}
    ).json()
    post.sentiment = resp
    post.save()
