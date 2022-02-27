from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("network", views.NetworkViewSet, basename="network")
router.register("channel", views.ChannelViewSet, basename="channel")
router.register("tag", views.TagViewSet, basename="tag")
router.register("post", views.PostViewSet, basename="post")
urlpatterns = [
    path("count_post/", views.PostCountAPIView.as_view(), name="count-post"),
    path("search_post/", views.SearchCountAPIView.as_view(), name="search-post"),
    path("keyword/", views.KeywordAPIView.as_view(), name="keyword"),
]

urlpatterns += router.urls
