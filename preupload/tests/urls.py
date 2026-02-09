from django.urls import path, include

urlpatterns = [
    path("preupload/", include("preupload.urls")),
]
