from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncHour, TruncMonth


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


def get_keyword_statics(qs, type, start=None, end=None):
    result = []
    if type == 'hourly':
        start = start or timezone.localtime()
        end = end or (start - timezone.timedelta(hours=12))
        qs = qs.filter(created_at__gte=start, created_at__lte=end).annotate(
            hour=TruncHour("created_at")
        )
        for hour in hourly_iterate(start, end):
            temp = qs.filter(hour__hour=hour.hour, hour__day=hour.day)
            temp = (
                temp.values('keyword')
                .annotate(count=Count('keyword'))
                .order_by('-count')
            )
            keywords = []
            for keyword in temp[: min(10, len(temp))]:
                keywords.append(
                    {'keyword': keyword['keyword'], 'count': keyword['count']}
                )
            result.append(
                {
                    'hour': hour,
                    'keywords': keywords,
                }
            )
    elif type == 'daily':
        start = start or timezone.localtime()
        end = end or (start - timezone.timedelta(days=7))
        qs = qs.filter(created_at__gte=start, created_at__lte=end).annotate(
            day=TruncDate("created_at")
        )
        for day in daily_iterate(start, end):
            temp = qs.filter(day__month=day.month, day__day=day.day)
            temp = (
                temp.values('keyword')
                .annotate(count=Count('keyword'))
                .order_by('-count')
            )
            keywords = []
            for keyword in temp[: min(10, len(temp))]:
                keywords.append(
                    {'keyword': keyword['keyword'], 'count': keyword['count']}
                )
            result.append(
                {
                    'day': day,
                    'keywords': keywords,
                }
            )
    elif type == 'monthly':
        start = start or timezone.localtime()
        end = end or (start - relativedelta(months=7))
        qs = qs.filter(created_at__gte=start, created_at__lte=end).annotate(
            month=TruncMonth("created_at")
        )
        for month in monthly_iterate(start, end):
            temp = qs.filter(month__year=month.year, month__month=month.month)
            temp = (
                temp.values('keyword')
                .annotate(count=Count('keyword'))
                .order_by('-count')
            )
            keywords = []
            for keyword in temp[: min(10, len(temp))]:
                keywords.append(
                    {'keyword': keyword['keyword'], 'count': keyword['count']}
                )
            result.append(
                {
                    'month': month,
                    'keywords': keywords,
                }
            )
    return result
