from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("network", views.NetworkViewSet, basename="network")
router.register("channel", views.ChannelViewSet, basename="channel")
router.register("post", views.PostViewSet, basename="post")
urlpatterns = []

urlpatterns += router.urls
