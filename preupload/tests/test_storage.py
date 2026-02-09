from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from preupload.storage import storage, PREFIX


class PreuploadStorageTestCase(TestCase):
    @override_settings(
        PREUPLOAD={
            "STORAGE": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {"location": "/tmp/preupload_test"},
            },
        },
    )
    def test_save_open_delete(self):
        content = b"hello world"
        f = SimpleUploadedFile("test.txt", content, content_type="text/plain")
        ref = storage.save(f, name="test.txt")
        self.assertTrue(ref.startswith(PREFIX))
        try:
            opened = storage.open(ref)
            self.assertEqual(opened.read(), content)
            opened.close()
        finally:
            storage.delete(ref)

    @override_settings(
        PREUPLOAD={
            "STORAGE": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {"location": "/tmp/preupload_test"},
            },
        },
    )
    def test_storage_instance(self):
        content = b"module test"
        f = SimpleUploadedFile("m.txt", content)
        ref = storage.save(f, name="m.txt")
        self.assertTrue(ref.startswith(PREFIX))
        try:
            opened = storage.open(ref)
            self.assertEqual(opened.read(), content)
            opened.close()
        finally:
            storage.delete(ref)
