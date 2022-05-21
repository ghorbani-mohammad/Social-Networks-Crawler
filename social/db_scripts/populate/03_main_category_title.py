import os
import sys
import django
import logging
from django.utils import timezone


def initial():
    sys.path.append("../..")
    os.environ["DJANGO_SETTINGS_MODULE"] = "social.settings"
    django.setup()


initial()

logger = logging.getLogger(__name__)

from network.models import Post
from network.tasks import extract_categories

two_month_ago = timezone.now() - timezone.timedelta(days=60)

for post in Post.objects.filter(
    created_at__gte=two_month_ago, main_category_title__isnull=True
):
    try:
        extract_categories(post.id)
    except Exception as e:
        print(e)
        logger.error(e)
