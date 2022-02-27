from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour, TruncMonth

from network.models import Network, Channel

KEYWORD_NUMBER = 20
CHANNEL_NUMBER = 5


def get_search_excluded_qs(apiview):
    qs = apiview.get_queryset()
    for backend in list(apiview.filter_backends):
        if backend.__name__ != 'SearchFilter':
            qs = backend().filter_queryset(apiview.request, qs, apiview)
    return qs


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


def get_count_statics(qs, search_excluded_qs, type, start=None, end=None):
    result = []
    if type == 'hourly':
        start = start or timezone.localtime()
        end = end or (start - timezone.timedelta(hours=12))
        qs = qs.filter(created_at__gte=start, created_at__lte=end)
        s_e_qs = search_excluded_qs.filter(created_at__gte=start, created_at__lte=end)
        qs = (
            qs.annotate(hour=TruncHour("created_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )
        s_e_qs = s_e_qs.annotate(hour=TruncHour("created_at"))
        for hour in hourly_iterate(start, end):
            count = qs.filter(hour__hour=hour.hour, hour__day=hour.day).first()
            count = count['count'] if count else 0
            total_count = s_e_qs.filter(
                hour__hour=hour.hour, hour__day=hour.day
            ).count()
            temp_result = {'hour': hour, 'count': count, 'total_count': total_count}
            networks = {}
            for network in Network.objects.all():
                networks[network.name] = s_e_qs.filter(
                    hour__hour=hour.hour, hour__day=hour.day, channel__network=network
                ).count()
            temp_result['networks'] = networks
            channels = {}
            for channel in Channel.objects.all():
                channels[channel.name] = s_e_qs.filter(
                    hour__hour=hour.hour, hour__day=hour.day, channel=channel
                ).count()
            temp_result['channels'] = channels
            result.append(temp_result)
    elif type == 'daily':
        start = start or timezone.localtime()
        end = end or (start - timezone.timedelta(days=7))
        qs = qs.filter(created_at__gte=start, created_at__lte=end)
        s_e_qs = search_excluded_qs.filter(created_at__gte=start, created_at__lte=end)
        qs = (
            qs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        s_e_qs = s_e_qs.annotate(day=TruncDate("created_at"))
        for day in daily_iterate(start, end):
            count = qs.filter(day__month=day.month, day__day=day.day).first()
            count = count['count'] if count else 0
            total_count = s_e_qs.filter(day__month=day.month, day__day=day.day).count()
            temp_result = {'day': day, 'count': count, 'total_count': total_count}
            for network in Network.objects.all():
                temp_result[network.name] = s_e_qs.filter(
                    day__month=day.month, day__day=day.day, channel__network=network
                ).count()
            result.append(temp_result)
    elif type == 'monthly':
        start = start or timezone.localtime()
        end = end or (start - relativedelta(months=7))
        qs = qs.filter(created_at__gte=start, created_at__lte=end)
        s_e_qs = search_excluded_qs.filter(created_at__gte=start, created_at__lte=end)
        qs = (
            qs.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        s_e_qs = s_e_qs.annotate(month=TruncMonth("created_at"))
        for month in monthly_iterate(start, end):
            count = qs.filter(month__year=month.year, month__month=month.month).first()
            count = count['count'] if count else 0
            total_count = s_e_qs.filter(
                month__year=month.year, month__month=month.month
            ).count()
            temp_result = {'month': month, 'count': count, 'total_count': total_count}
            for network in Network.objects.all():
                temp_result[network.name] = s_e_qs.filter(
                    month__year=month.year,
                    month__month=month.month,
                    channel__network=network,
                ).count()
            result.append(temp_result)
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
            for keyword in temp[: min(KEYWORD_NUMBER, len(temp))]:
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
            for keyword in temp[: min(KEYWORD_NUMBER, len(temp))]:
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
            for keyword in temp[: min(KEYWORD_NUMBER, len(temp))]:
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


def get_channels_statistics(queryset):
    total = 0
    channels = (
        queryset.values('channel', 'channel__name')
        .annotate(count=Count('channel'))
        .order_by('-count')
    )
    channels = channels[: min(CHANNEL_NUMBER, len(channels))]
    channels = [
        {'channel': channel['channel__name'], 'count': channel['count']}
        for channel in channels
    ]
    for channel in channels:
        total += channel['count']
    return {'channels': channels, 'total': total}
