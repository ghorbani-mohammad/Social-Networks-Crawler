from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('secret-admin/', admin.site.urls),
    path("api/v1/net/", include("network.urls")),
]
