import json
import random
import os
import sys
from datetime import datetime
from openpyxl import load_workbook

import django


def initial():
    sys.path.append('../..')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'social.settings'
    django.setup()


initial()

from network.models import Channel, Post

channel_ids = list(
    Channel.objects.filter(network__name='Telegram').values_list('id', flat=True)
)
print(channel_ids)
print(random.choice(channel_ids))

sheet = load_workbook(filename='/app/Book1.xlsx').active
texts = [cell.value for cell in sheet['C']]
dates = [cell.value for cell in sheet['B']]

for index, text in enumerate(texts[:10]):
    index = index + 1
    date = dates[index]
    text = text[index]
    # print(date)
    # print(datetime.strptime(date, "%Y-%B-%d %H:%M:%S"))
    Post.objects.create(
        body=text, channel_id=random.choice(channel_ids), created_at=date, imported=True
    )
