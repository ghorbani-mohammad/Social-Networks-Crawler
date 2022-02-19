import requests

from celery import shared_task
from celery.utils.log import get_task_logger

from . import models

logger = get_task_logger(__name__)


@shared_task(name="extract_keywords")
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
