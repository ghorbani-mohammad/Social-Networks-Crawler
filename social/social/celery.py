from __future__ import absolute_import

import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social.settings")
app = Celery("social")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


app.conf.beat_schedule = {
    "check_channels_crawl": {
        "task": "network.tasks.check_channels_crawl",
        "schedule": crontab(minute="*/30"),
    },
    "get_linkedin_feed": {
        "task": "linkedin.tasks.get_linkedin_feed",
        "schedule": crontab(minute="*/20"),
    },
}
