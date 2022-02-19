from django_filters import FilterSet, DateTimeFromToRangeFilter, CharFilter

from . import models


def filter_by_channel_ids(queryset, name, value):
    values = value.split(',')
    return queryset.filter(channel_id__in=values)


def filter_by_network_ids(queryset, name, value):
    values = value.split(',')
    return queryset.filter(channel__network_id__in=values)


class PostFilter(FilterSet):
    date = DateTimeFromToRangeFilter(field_name="created_at")
    channels = CharFilter(method=filter_by_channel_ids)
    networks = CharFilter(method=filter_by_network_ids)

    class Meta:
        model = models.Post
        fields = ["channels", "networks", "date"]


def keyword_filter_by_channel_ids(queryset, name, value):
    values = value.split(',')
    return queryset.filter(post__channel_id__in=values)


def keyword_filter_by_network_ids(queryset, name, value):
    values = value.split(',')
    return queryset.filter(post__channel__network_id__in=values)


class KeywordFilter(FilterSet):
    date = DateTimeFromToRangeFilter(field_name="created_at")
    channels = CharFilter(method=keyword_filter_by_channel_ids)
    networks = CharFilter(method=keyword_filter_by_network_ids)

    class Meta:
        model = models.Keyword
        fields = ["channels", "networks", "date"]
