import requests
import subprocess
from io import BytesIO

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.files.base import File
from celery import Task
from celery import shared_task
from celery.utils.log import get_task_logger
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

from . import models
from twitter import tasks as twi_tasks
from linkedin import tasks as lin_tasks

logger = get_task_logger(__name__)

NER_KEY_MAPPING = {
    "date": "تاریخ",
    "time": "زمان",
    "event": "رویداد",
    "money": "مالی",
    "person": "شخص",
    "percent": "درصد",
    "product": "محصول",
    "facility": "تسهیلات",
    "location": "مکان",
    "organization": "سازمان",
    "FAC": "سازه",
    "ORG": "سازمان",
    "GPE": "مکان",
    "LOC": "مکان",
    "EVENT": "رویداد",
    "MONEY": "مالی",
}


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 10}
    retry_backoff = 5
    default_retry_delay = 60
    retry_jitter = True


@shared_task(base=BaseTaskWithRetry)
def extract_keywords(post_id):
    post = models.Post.objects.get(id=post_id)
    ignored_keywords = list(models.IgnoredKeyword.objects.values_list("keyword"))
    endpoint = None
    if post.channel.language == models.Channel.PERSIAN:
        endpoint = "http://persian_analyzer_api/v1/app/keyword/"
    if post.channel.language == models.Channel.ENGLISH:
        endpoint = "http://analyzer_api/api/v1/keyword/"
    resp = requests.post(endpoint, {"text": post.body}).json()
    objs = []
    for keyword in resp["keywords"]:
        if keyword not in ignored_keywords:
            objs.append(models.Keyword(post=post, keyword=keyword))
    if "keyphrases" in resp:
        for keyphrase in resp["keyphrases"]:
            if keyphrase not in ignored_keywords:
                objs.append(models.Keyword(post=post, keyword=keyphrase))
    models.Keyword.objects.bulk_create(objs)


@shared_task(base=BaseTaskWithRetry)
def extract_ner(post_id):
    with transaction.atomic():
        post = models.Post.objects.select_for_update().get(id=post_id)
        endpoint = None
        if post.channel.language == models.Channel.PERSIAN:
            endpoint = "http://persian_analyzer_api/v1/app/ner/"
        if post.channel.language == models.Channel.ENGLISH:
            endpoint = "http://analyzer_api/api/v1/ner/"
        resp = requests.post(endpoint, {"text": post.body}).json()
        temp = {}
        for key in NER_KEY_MAPPING.keys():
            if key in resp:
                temp[NER_KEY_MAPPING[key]] = list(set(resp.pop(key)))
        post.ner = temp
        post.save()


@shared_task(base=BaseTaskWithRetry)
def extract_sentiment(post_id):
    with transaction.atomic():
        post = models.Post.objects.select_for_update().get(id=post_id)
        resp = requests.post(
            "http://persian_analyzer_api/v1/app/sentiment/", {"text": post.body}
        ).json()
        post.sentiment = resp
        post.save()


@shared_task(base=BaseTaskWithRetry)
def extract_categories(post_id):
    with transaction.atomic():
        post = models.Post.objects.select_for_update().get(id=post_id)
        resp = requests.post(
            "http://persian_analyzer_api/v1/app/classification/", {"text": post.body}
        ).json()
        sorted_result = sorted(resp, key=lambda k: k["score"], reverse=True)
        post.category = sorted_result
        post.main_category_title = sorted_result[0]["label"]
        post.save()


@shared_task()
def check_channels_crawl():
    channels = models.Channel.objects.filter(last_crawl__isnull=False)
    for channel in channels:
        interval = timezone.localtime() - channel.last_crawl
        hours = interval.total_seconds() / 3600
        if hours >= channel.crawl_interval:
            print(f"******* channel {channel} must crawled")
            if channel.network.name == "Twitter":
                twi_tasks.get_twitter_posts(channel.pk)
            elif channel.network.name == "Linkedin":
                lin_tasks.get_linkedin_posts(channel.pk)


@shared_task()
def take_backup(backup_id):
    backup = models.Backup.objects.get(pk=backup_id)
    date_time = backup.created_at.strftime("%d-%m-%Y-%H_%M_%S")
    if backup.type == models.Backup.RASAD_1:
        subprocess.run(
            [
                "ssh",
                "-i",
                "/app/secrets/id_rsa_social_api",
                "-o",
                "StrictHostKeyChecking=no",
                f"root@{settings.SERVER_IP}",
                f"docker exec -t postgres pg_dumpall -c -U postgres | gzip > /root/army/frontend/dist/backup/postgres_db_{date_time}.sql.gz",
            ]
        )
        backup.link = (
            f"http://{settings.SERVER_IP}/backup/postgres_db_{date_time}.sql.gz"
        )
    elif backup.type == models.Backup.RASAD_2:
        subprocess.run(
            [
                "ssh",
                "-i",
                "/app/secrets/id_rsa_social_api",
                "-o",
                "StrictHostKeyChecking=no",
                f"root@{settings.SERVER_IP}",
                f"docker exec -t social_db pg_dumpall -c -U postgres | gzip > /root/army/frontend/dist/backup/social_db_{date_time}.sql.gz",
            ]
        )
        backup.link = f"http://{settings.SERVER_IP}/backup/social_db_{date_time}.sql.gz"
    backup.status = models.Backup.COMPLETED
    backup.save()


@shared_task()
def export_channel_list(export_id):
    channels = models.Channel.objects.all()
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.freeze_panes = worksheet["B2"]
    worksheet.title = "Channel List Report"
    fields_name = ["Number", "Name", "Network", "Status"]
    for col_num, column_title in enumerate(fields_name, start=1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        cell.border = Border(bottom=Side(border_style="medium", color="FF000000"))
        cell.value = column_title
    for row_index, channel in enumerate(channels, start=2):
        guest_fields = [
            row_index - 1,
            channel.name,
            channel.network.name,
            channel.status,
        ]
        for col_index, column in enumerate(guest_fields, start=1):
            cell = worksheet.cell(row=row_index, column=col_index)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
            cell.value = column
    virtual_workbook = BytesIO()
    workbook.save(virtual_workbook)
    export = models.ChannelListExport.objects.get(pk=export_id)
    export.file.save("excel.xlsx", File(virtual_workbook))
    export.save()


@shared_task()
def remove_ignored_keywords():
    ignored_keywords = list(models.IgnoredKeyword.objects.values_list("keyword"))
    first_id = models.Keyword.objects.first().id
    last_id = models.Keyword.objects.last().id
    batch_size = 10000
    current_counter = first_id
    while current_counter < last_id:
        print(current_counter)
        for item in models.Keyword.objects.filter(
            id__gte=current_counter, id__lte=current_counter + batch_size
        ):
            if item.keyword in ignored_keywords:
                item.delete()
        current_counter += batch_size
