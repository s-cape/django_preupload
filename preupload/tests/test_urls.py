from django.test import TestCase
from django.urls import reverse, resolve

from preupload import views


class UrlsTestCase(TestCase):
    def test_preupload_url_resolves_to_view(self):
        url = reverse("preupload:preupload")
        self.assertEqual(url, "/preupload/preupload/")
        self.assertEqual(resolve(url).func, views.preupload)
