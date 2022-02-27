import os
import sys
import datetime
from django.utils.timezone import make_aware

import django


def initial():
    sys.path.append('../..')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'social.settings'
    django.setup()


initial()

from network.models import Keyword


today = datetime.date.today()

keywords = Keyword.objects.filter(created_at__date=today)

print(keywords.count())
