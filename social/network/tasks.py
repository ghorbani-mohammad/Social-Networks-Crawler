import requests

from celery import shared_task
from celery.utils.log import get_task_logger

from . import models

logger = get_task_logger(__name__)


@shared_task(
    name="extract_keywords",
    autoretry_for=(Exception,),
    default_retry_delay=60,
    retry_kwargs={'max_retries': 10},
)
def extract_keywords(post_id):
    post = models.Post.objects.get(id=post_id)
    if len(post.body) < 100:
        return
    resp = requests.post(
        "http://analyzer_api/api/v1/keword_extraction/", {"body": post.body}
    ).json()
    objs = []
    for keyword in resp['keywords']:
        objs.append(models.Keyword(post=post, keyword=keyword))
    models.Keyword.objects.bulk_create(objs)


def extract_ner(post_id):
    post = models.Post.objects.get(id=post_id)
    if len(post.body) < 100:
        return
    resp = requests.post(
        "http://persian_analyzer_api/v1/app/ner/", {"text": post.body}
    ).json()
    print(resp)
