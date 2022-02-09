from django_filters import FilterSet, DateFromToRangeFilter

from . import models


class PostCountFilter(FilterSet):
    date = DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = models.Post
        fields = ["channel", "channel__network", "date"]
