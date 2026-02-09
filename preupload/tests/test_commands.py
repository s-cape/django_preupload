from io import BytesIO, StringIO
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command

from preupload.models import Preupload
from preupload.storage import storage


class CleanupCommandTestCase(TestCase):
    @override_settings(
        PREUPLOAD={
            "STORAGE": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {"location": "/tmp/preupload_test_cleanup"},
            },
        },
    )
    def test_cleanup_expired(self):
        ref = storage.save(BytesIO(b"x"), name="x.txt")
        p = Preupload.objects.create(
            token="t",
            storage_ref=ref,
            original_filename="x.txt",
        )
        Preupload.objects.filter(pk=p.pk).update(
            created_at=timezone.now() - timedelta(minutes=61)
        )
        call_command("cleanup_preuploads", stdout=StringIO(), stderr=StringIO())
        self.assertEqual(Preupload.objects.count(), 0)

    def test_cleanup_dry_run(self):
        ref = storage.save(BytesIO(b"x"), name="x.txt")
        p = Preupload.objects.create(
            token="t2",
            storage_ref=ref,
            original_filename="x.txt",
        )
        Preupload.objects.filter(pk=p.pk).update(
            created_at=timezone.now() - timedelta(minutes=61)
        )
        call_command(
            "cleanup_preuploads", "--dry-run", stdout=StringIO(), stderr=StringIO()
        )
        self.assertEqual(Preupload.objects.count(), 1)
