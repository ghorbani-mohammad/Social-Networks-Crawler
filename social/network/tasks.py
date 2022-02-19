from celery import shared_task
from celery.utils.log import get_task_logger

from . import models

logger = get_task_logger(__name__)


@shared_task(name="extract_keywords")
def extract_keywords(post_id):
    post = models.Post.objects.get(id=post_id)
