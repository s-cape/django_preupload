from django.urls import path, include

from . import views as test_views

urlpatterns = [
    path("preupload/", include("preupload.urls")),
    path("form/", test_views.form_page, name="form"),
]
