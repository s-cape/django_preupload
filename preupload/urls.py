from django.urls import path

from . import views

app_name = "preupload"

urlpatterns = [
    path("preupload/", views.preupload, name="preupload"),
]
