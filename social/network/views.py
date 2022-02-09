from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters as rf_filters
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination

from . import models, serializers, filters, utils


class ListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class NetworkViewSet(ModelViewSet):
    queryset = models.Network.objects.order_by("-id")
    serializer_class = serializers.NetworkSerializer
    pagination_class = ListPagination
    filter_backends = [
        rf_filters.SearchFilter,
        DjangoFilterBackend,
        rf_filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["name"]
    ordering_fields = ["name"]


class ChannelViewSet(ModelViewSet):
    queryset = models.Channel.objects.order_by("-id")
    serializer_class = serializers.ChannelSerializer
    pagination_class = ListPagination
    filter_backends = [
        rf_filters.SearchFilter,
        DjangoFilterBackend,
        rf_filters.OrderingFilter,
    ]
    filterset_fields = ["status", "network"]
    search_fields = ["username"]
    ordering_fields = ["username"]


class PostViewSet(ModelViewSet):
    queryset = models.Post.objects.order_by("-id")
    serializer_class = serializers.PostSerializer
    pagination_class = ListPagination
    filter_backends = [
        rf_filters.SearchFilter,
        DjangoFilterBackend,
        rf_filters.OrderingFilter,
    ]
    filterset_fields = ["channel", "channel__network"]
    search_fields = ["body"]
    ordering_fields = ["views_count", "share_count"]


class PostCountAPIView(ListAPIView):
    queryset = models.Post.objects.order_by("-id")
    serializer_class = serializers.PostSerializer
    pagination_class = ListPagination
    filter_backends = [rf_filters.SearchFilter, DjangoFilterBackend]
    filterset_class = filters.PostCountFilter
    search_fields = ["body"]

    def list(self, request):
        serializer = serializers.PostCountInputSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = super().list(request)
        qs = self.filter_queryset(self.get_queryset())
        response.data['statics'] = utils.get_count_statics(
            qs, data['type'], data['date_after'], data['date_end']
        )
        return response
