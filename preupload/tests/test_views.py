from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from preupload import tokens


class PreuploadViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_post_no_file_returns_400(self):
        response = self.client.post(reverse("preupload:preupload"), data={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "No file uploaded"})

    def test_post_file_too_large_returns_413(self):
        # Test settings set MAX_UPLOAD_SIZE to 1MB
        file = SimpleUploadedFile("big.txt", b"x" * (1024 * 1024 + 1), "text/plain")
        response = self.client.post(
            reverse("preupload:preupload"),
            data={"file": file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 413)
        data = response.json()
        self.assertEqual(data["error"], "File too large")
        self.assertEqual(data["max_size"], 1024 * 1024)

    def test_post_valid_file_returns_200_and_token(self):
        file = SimpleUploadedFile("a.txt", b"content", "text/plain")
        response = self.client.post(
            reverse("preupload:preupload"),
            data={"file": file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertEqual(data["original_filename"], "a.txt")
        preupload = tokens.resolve_preupload_token(data["token"])
        self.assertIsNotNone(preupload)
        self.assertEqual(preupload.original_filename, "a.txt")
