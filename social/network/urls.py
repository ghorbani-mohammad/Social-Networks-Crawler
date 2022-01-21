from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
urlpatterns = []

urlpatterns += router.urls
