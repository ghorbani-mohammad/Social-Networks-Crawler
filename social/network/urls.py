from django.urls import path
from rest_framework.routers import SimpleRouter
from django.views.decorators.cache import cache_page

from . import views

router = SimpleRouter()
router.register("tag", views.TagViewSet, basename="tag")
router.register("post", views.PostViewSet, basename="post")
router.register("network", views.NetworkViewSet, basename="network")
router.register("channel", views.ChannelViewSet, basename="channel")
router.register("backup", views.BackupViewSet, basename="backup")
urlpatterns = [
    path("test_error/", views.TestErrorView.as_view()),
    path(
        "count_post/",
        cache_page(20 * 60)(views.PostCountAPIView.as_view()),
        name="count-post",
    ),
    path(
        "search_post/",
        cache_page(20 * 60)(views.SearchCountAPIView.as_view()),
        name="search-post",
    ),
    path(
        "keyword/", cache_page(20 * 60)(views.KeywordAPIView.as_view()), name="keyword"
    ),
]

urlpatterns += router.urls
