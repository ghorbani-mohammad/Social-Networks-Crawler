from django_filters import FilterSet, DateTimeFromToRangeFilter

from . import models


class PostCountFilter(FilterSet):
    date = DateTimeFromToRangeFilter(field_name="created_at")

    class Meta:
        model = models.Post
        fields = ["channel", "channel__network", "date"]


class KeywordFilter(FilterSet):
    date = DateTimeFromToRangeFilter(field_name="created_at")

    class Meta:
        model = models.Keyword
        fields = ["post__channel", "post__channel__network", "date"]
