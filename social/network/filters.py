from django_filters import FilterSet, DateTimeFromToRangeFilter

from . import models


class PostCountFilter(FilterSet):
    date = DateTimeFromToRangeFilter(field_name="created_at")

    class Meta:
        model = models.Post
        fields = ["channel", "channel__network", "date"]
