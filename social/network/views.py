from django.utils import timezone
from rest_framework import filters as rf_filters
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

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


class TagViewSet(ModelViewSet):
    queryset = models.Tag.objects.order_by("-id")
    serializer_class = serializers.TagSerializer
    pagination_class = ListPagination
    filter_backends = [
        rf_filters.SearchFilter,
        rf_filters.OrderingFilter,
    ]
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
    filterset_class = filters.ChannelFilter
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
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.PostFilter

    def list(self, request):
        serializer = serializers.PostCountInputSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = super().list(request)
        qs = self.filter_queryset(self.get_queryset())
        search_excluded_qs = utils.get_search_excluded_qs(self)
        response.data["statics"] = utils.get_count_statics(
            qs,
            search_excluded_qs,
            data["type"],
            data["date_after"],
            data["date_before"],
        )
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        response.data["today_posts"] = (
            self.get_queryset().filter(created_at__gte=today).count()
        )
        response.data["channel_posts"] = (
            (models.Channel.objects.get(pk=request.GET["channel"]).today_posts_count)
            if "channel" in request.GET
            else self.get_queryset().count()
        )
        response.data["network_posts"] = (
            (
                models.Network.objects.get(
                    pk=request.GET["channel__network"]
                ).today_posts_count
            )
            if "channel__network" in request.GET
            else self.get_queryset().count()
        )
        return response


class SearchCountAPIView(ListAPIView):
    serializer_class = serializers.PostSerializer
    pagination_class = ListPagination
    filter_backends = [rf_filters.SearchFilter, DjangoFilterBackend]
    filterset_class = filters.PostFilter
    search_fields = ["body"]

    def filter_queryset(self, qs):
        return utils.get_search_modified_qs(self, qs)

    def get_queryset(self):
        return models.Post.objects.order_by("-id")

    def list(self, request):
        serializer = serializers.PostCountInputSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = super().list(request)
        qs = self.filter_queryset(self.get_queryset())
        search_excluded_qs = utils.get_search_excluded_qs(self)
        response.data["statics"] = utils.get_count_statics(
            qs,
            search_excluded_qs,
            data["type"],
            data["date_after"],
            data["date_before"],
        )
        response.data["channels_statistics"] = utils.get_channels_statistics(qs)
        return response


class KeywordAPIView(ListAPIView):
    queryset = models.Keyword.objects.order_by("-id")
    serializer_class = serializers.KeywordSerializer
    pagination_class = ListPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.KeywordFilter

    def list(self, request):
        serializer = serializers.PostCountInputSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = super().list(request)
        qs = self.filter_queryset(self.get_queryset())
        response.data["statics"] = utils.get_keyword_statics(
            qs, data["type"], data["date_after"], data["date_before"]
        )
        return response


class BackupViewSet(ModelViewSet):
    queryset = models.Backup.objects.order_by("-id")
    serializer_class = serializers.BackupSerializer
    pagination_class = ListPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type", "status"]
