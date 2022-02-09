from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour, TruncMonth

from . import models


def hourly_iterate(start, finish):
    result = []
    start = start.replace(minute=0, second=0, microsecond=0)
    while start <= finish:
        result.append(start)
        start += timezone.timedelta(hours=1)
    return result


def daily_iterate(start, finish):
    result = []
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    while start <= finish:
        result.append(start)
        start += timezone.timedelta(days=1)
    return result


def monthly_iterate(start, finish):
    result = []
    start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while start <= finish:
        result.append(start)
        start += relativedelta(months=1)
    return result


def get_count_statics(qs, type, start=None, end=None):
    result = []
    if type == 'hourly':
        # todo: remove start and end
        start = models.Post.objects.first().created_at
        end = start + timezone.timedelta(hours=20)
        start = start or timezone.localtime()
        end = end or (start - timezone.timedelta(hours=12))
        qs = qs.filter(created_at__gte=start, created_at__lte=end)
        qs = (
            qs.annotate(hour=TruncHour("created_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )
        for hour in hourly_iterate(start, end):
            count = qs.filter(hour__hour=hour.hour, hour__day=hour.day).first()
            result.append({'hour': hour, 'count': count['count'] if count else 0})
    elif type == 'daily':
        # todo: remove start and end
        start = models.Post.objects.first().created_at
        end = start + timezone.timedelta(days=10)
        start = start or timezone.localtime()
        end = end or (start - timezone.timedelta(days=7))
        qs = qs.filter(created_at__gte=start, created_at__lte=end)
        qs = (
            qs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        for day in daily_iterate(start, end):
            count = qs.filter(day__month=day.month, day__day=day.day).first()
            result.append({'day': day, 'count': count['count'] if count else 0})
    elif type == 'monthly':
        # todo: remove start and end
        start = models.Post.objects.first().created_at - relativedelta(months=10)
        end = timezone.localtime()
        start = start or timezone.localtime()
        end = end or (start - relativedelta(months=7))
        qs = qs.filter(created_at__gte=start, created_at__lte=end)
        qs = (
            qs.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        for month in monthly_iterate(start, end):
            count = qs.filter(month__year=month.year, month__month=month.month).first()
            result.append({'month': month, 'count': count['count'] if count else 0})
    return result
