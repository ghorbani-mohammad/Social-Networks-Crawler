import os
import sys
import django
from time import sleep


def initial():
    sys.path.append("../..")
    os.environ["DJANGO_SETTINGS_MODULE"] = "social.settings"
    django.setup()


initial()

from network.models import Channel, Post
from network.tasks import extract_ner, extract_keywords

english_posts = Post.objects.filter(channel__language=Channel.ENGLISH)
for post in english_posts:
    post.keywords.all().delete()
    extract_keywords.delay(post.id)

sleep(100)

for post in english_posts:
    extract_ner.delay(post.id)
