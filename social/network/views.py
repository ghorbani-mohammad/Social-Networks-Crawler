from rest_framework import filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from . import models, serializers


class ListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class NetworkViewSet(ModelViewSet):
    queryset = models.Network.objects.order_by("-id")
    serializer_class = serializers.PackageSerializer
    pagination_class = ListPagination
    filter_backends = [
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["name"]
    ordering_fields = ["name"]
