import os
import sys
import random
from openpyxl import load_workbook
from django.utils.timezone import make_aware

import django


def initial():
    sys.path.append("../..")
    os.environ["DJANGO_SETTINGS_MODULE"] = "social.settings"
    django.setup()


initial()

from network.models import Channel, Post

channel_ids = list(
    Channel.objects.filter(network__name="Telegram").values_list("id", flat=True)
)

sheet = load_workbook(filename="/app/messages.xlsx").active
texts = [cell.value for cell in sheet["F"]]
dates = [cell.value for cell in sheet["C"]]

success_counter = 0
failure_counter = 0
for index, text in enumerate(texts):
    try:
        index = index + 1
        date = dates[index]
        text = texts[index]
        post = Post.objects.create(
            body=text, channel_id=random.choice(channel_ids), imported=True
        )
        Post.objects.filter(pk=post.pk).update(
            created_at=make_aware(date), updated_at=make_aware(date)
        )
        success_counter += 1
    except:
        failure_counter += 1

print(f"success counter: {success_counter}")
print(f"failure counter: {failure_counter}")
