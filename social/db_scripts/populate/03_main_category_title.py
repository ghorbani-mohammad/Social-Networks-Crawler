import os
import sys
import django
from django.utils import timezone


def initial():
    sys.path.append("../..")
    os.environ["DJANGO_SETTINGS_MODULE"] = "social.settings"
    django.setup()


initial()

from network.models import Post
from network.tasks import extract_categories

two_month_ago = timezone.now() - timezone.timedelta(days=60)

for post in Post.objects.filter(created_at__gte=two_month_ago):
    extract_categories(post.id)
